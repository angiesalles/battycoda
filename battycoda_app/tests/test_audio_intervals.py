"""Regressions for malformed imported annotations and empty task audio windows."""

import io
import pickle
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import h5py
import numpy as np
import soundfile as sf
from django.test import RequestFactory, SimpleTestCase, override_settings
from PIL import Image

from battycoda_app.audio.modules.file_utils import process_pickle_file
from battycoda_app.simple_api.recording_upload import _process_pickle_segmentation
from battycoda_app.views_audio import task_audio_snippet_view, task_spectrogram_view
from battycoda_app.views_batch_upload.file_processing import create_segmentation_from_pickle


class PickleIntervalTests(SimpleTestCase):
    def read_intervals(self, onsets, offsets, duration=None):
        source = io.BytesIO(pickle.dumps({"onsets": onsets, "offsets": offsets}))
        source.name = "annotations.pickle"
        return process_pickle_file(source, max_duration=duration)

    def test_invalid_intervals_rejected_without_recording_duration(self):
        for onset, offset in [(14819.495, -223.735), (-1, 1), (1, 1), (2, 1)]:
            with self.subTest(onset=onset, offset=offset):
                with self.assertRaisesRegex(ValueError, "annotations.pickle.*Segment 1"):
                    self.read_intervals([onset], [offset])

    def test_nonfinite_times_rejected(self):
        for value in [float("nan"), float("inf"), float("-inf")]:
            for onset, offset in [(value, 1), (0, value)]:
                with self.subTest(onset=onset, offset=offset):
                    with self.assertRaisesRegex(ValueError, "finite"):
                        self.read_intervals([onset], [offset])

    def test_recording_bounds_rejected(self):
        for onset, offset in [(0, 61), (60, 61), (15000, 15001)]:
            with self.subTest(onset=onset, offset=offset):
                with self.assertRaisesRegex(ValueError, "recording duration"):
                    self.read_intervals([onset], [offset], duration=60)

    def test_valid_intervals_preserved(self):
        for duration in [None, 60]:
            with self.subTest(duration=duration):
                self.assertEqual(self.read_intervals([0, 59.5], [0.01, 60], duration), ([0.0, 59.5], [0.01, 60.0]))


class BatchImportIntervalTests(SimpleTestCase):
    def test_out_of_bounds_import_rejected_before_database_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            wav_path = Path(directory) / "recording.wav"
            sf.write(wav_path, np.zeros(8000), 8000)
            pickle_path = Path(directory) / "recording.wav.pickle"
            pickle_path.write_bytes(pickle.dumps({"onsets": [0.25], "offsets": [1.5]}))
            # Duration is not populated yet during a batch upload.
            recording = SimpleNamespace(wav_file=SimpleNamespace(path=str(wav_path)), duration=None)
            with patch("battycoda_app.views_batch_upload.file_processing.Segmentation.objects.create") as create:
                with self.assertRaisesRegex(ValueError, "recording duration"):
                    create_segmentation_from_pickle(recording, str(pickle_path), pickle_path.name, None)
                create.assert_not_called()


class APIImportIntervalTests(SimpleTestCase):
    def test_out_of_bounds_import_rejected_before_database_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            wav_path = Path(directory) / "recording.wav"
            sf.write(wav_path, np.zeros(8000), 8000)
            recording = SimpleNamespace(wav_file=SimpleNamespace(path=str(wav_path)), duration=None)
            with patch("battycoda_app.simple_api.recording_upload.Segmentation.objects.create") as create:
                for onset, offset in [(0.25, 1.5), (0.024, 15000)]:
                    with self.subTest(onset=onset, offset=offset):
                        source = io.BytesIO(pickle.dumps({"onsets": [onset], "offsets": [offset]}))
                        source.name = "annotations.pickle"
                        result = _process_pickle_segmentation(source, recording, None)
                        self.assertIn("recording duration", result["error"])
                create.assert_not_called()


class TaskAudioIntervalTests(SimpleTestCase):
    def setUp(self):
        self.directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=self.directory))
        wav_path = Path(self.directory) / "recording.wav"
        sf.write(wav_path, np.sin(np.arange(8000) / 10), 8000)
        h5_dir = Path(self.directory) / "spectrograms" / "recordings"
        h5_dir.mkdir(parents=True)
        with h5py.File(h5_dir / "fixture.h5", "w") as data:
            data.attrs.update(sample_rate=8000, duration=1.0, n_frames=101, n_freq_bins=257, n_fft=512, hop_length=80)
            data.create_dataset("spectrogram", data=np.tile(np.arange(101, dtype=np.float16), (257, 1)))
        self.user = SimpleNamespace(
            is_authenticated=True, profile=SimpleNamespace(group=None, spectrogram_colormap="roseus")
        )
        self.task = SimpleNamespace(
            onset=0.25,
            offset=0.5,
            created_by=self.user,
            group=None,
            batch=SimpleNamespace(wav_file=SimpleNamespace(path=str(wav_path), name="recordings/recording.wav")),
            species=SimpleNamespace(
                detail_padding_start_ms=5,
                detail_padding_end_ms=5,
                overview_padding_start_ms=150,
                overview_padding_end_ms=150,
            ),
        )
        recording = SimpleNamespace(id=1, name="fixture", processing_status="ready", spectrogram_file="fixture.h5")
        self.enterContext(patch("django.shortcuts.get_object_or_404", return_value=self.task))
        manager = self.enterContext(patch("battycoda_app.models.recording.Recording.all_objects"))
        manager.filter.return_value.first.return_value = recording
        self.cache_path = Path(self.directory) / "snippet.wav"
        self.enterContext(patch("battycoda_app.audio.utils.appropriate_file", return_value=str(self.cache_path)))
        self.logger = self.enterContext(patch("battycoda_app.views_audio.logger"))

    def request(self, view, params=None):
        request = RequestFactory().get("/audio/task/885291/", params or {})
        request.user = self.user
        return view(request, 885291)

    def test_malformed_tasks_return_422_without_generating_audio(self):
        intervals = [(14819.495, -223.735), (-1, 0.5), (0.5, 0.5), (float("nan"), 0.5), (0, float("inf"))]
        with patch("battycoda_app.audio.modules.audio_processing.get_audio_bit") as extract:
            for onset, offset in intervals:
                self.task.onset, self.task.offset = onset, offset
                for view in [task_audio_snippet_view, task_spectrogram_view]:
                    with self.subTest(onset=onset, offset=offset, view=view.__name__):
                        response = self.request(view)
                        self.assertEqual(response.status_code, 422)
                        self.assertIn(b"invalid audio boundaries", response.content)
            extract.assert_not_called()
        self.logger.exception.assert_not_called()

    def test_out_of_bounds_tasks_return_422_even_with_cached_audio(self):
        self.cache_path.write_bytes(b"stale cached audio")
        for onset, offset in [(0.25, 1.5), (2, 3)]:
            self.task.onset, self.task.offset = onset, offset
            for view in [task_audio_snippet_view, task_spectrogram_view]:
                with self.subTest(onset=onset, offset=offset, view=view.__name__):
                    response = self.request(view)
                    self.assertEqual(response.status_code, 422)
        self.logger.exception.assert_not_called()

    def test_valid_spectrogram_and_overview_are_pngs(self):
        for overview in ["0", "1"]:
            with self.subTest(overview=overview):
                response = self.request(task_spectrogram_view, {"overview": overview})
                self.assertEqual(response.status_code, 200)
                with Image.open(io.BytesIO(response.content)) as image:
                    self.assertEqual(image.format, "PNG")
                    self.assertEqual(image.height, 257)
                    self.assertGreater(image.width, 0)

    def test_subframe_spectrogram_window_has_at_least_one_column(self):
        self.task.onset, self.task.offset = 0.5, 0.500001
        self.task.species.detail_padding_start_ms = 0
        self.task.species.detail_padding_end_ms = 0
        response = self.request(task_spectrogram_view)
        self.assertEqual(response.status_code, 200)
        with Image.open(io.BytesIO(response.content)) as image:
            self.assertEqual(image.width, 1)

    def test_valid_audio_is_playable_and_cached(self):
        for _ in range(2):
            response = self.request(task_audio_snippet_view)
            try:
                self.assertEqual(response.status_code, 200)
                audio = b"".join(response.streaming_content)
                self.assertGreater(sf.info(io.BytesIO(audio)).frames, 0)
            finally:
                response.close()
        self.assertTrue(self.cache_path.exists())

    def test_window_padding_can_extend_beyond_recording(self):
        self.task.onset, self.task.offset = 0, 1
        for view in [task_audio_snippet_view, task_spectrogram_view]:
            with self.subTest(view=view.__name__):
                response = self.request(view)
                try:
                    self.assertEqual(response.status_code, 200)
                finally:
                    response.close()

    def test_permission_check_precedes_interval_validation(self):
        self.task.created_by = object()
        self.task.onset, self.task.offset = 14819.495, -223.735
        for view in [task_audio_snippet_view, task_spectrogram_view]:
            with self.subTest(view=view.__name__):
                self.assertEqual(self.request(view).status_code, 403)
