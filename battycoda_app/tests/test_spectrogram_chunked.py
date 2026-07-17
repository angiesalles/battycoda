"""
Tests for chunked HDF5 spectrogram generation.

The core guarantee under test: streaming the STFT in small chunks produces
output frame-for-frame identical to a single-shot
librosa.stft(center=True, pad_mode="constant") over the whole file.
"""

import os
import tempfile

import h5py
import librosa
import numpy as np
import soundfile as sf
from django.test import SimpleTestCase

from battycoda_app.audio.task_modules.spectrogram.hdf5_generation_chunked import (
    DB_AMIN,
    HOP_LENGTH,
    N_FFT,
    N_FREQ_BINS,
    generate_hdf5_spectrogram_chunked,
)


def single_shot_reference(y):
    """Compute the spectrogram the non-chunked way, as float16 dB."""
    stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH, center=True, pad_mode="constant")
    db = librosa.amplitude_to_db(np.abs(stft), ref=1.0, amin=DB_AMIN, top_db=None)
    return db.astype(np.float16)


class ChunkedSpectrogramTest(SimpleTestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_wav(self, y, sr, channels=1):
        path = os.path.join(self.tmpdir.name, "test.wav")
        data = y if channels == 1 else np.stack([y, -0.5 * y], axis=1)
        sf.write(path, data, sr, subtype="PCM_16")
        return path

    def _run_chunked(self, wav_path, chunk_samples):
        out_path = os.path.join(self.tmpdir.name, "test.h5")
        result = generate_hdf5_spectrogram_chunked(wav_path, out_path, chunk_samples=chunk_samples)
        with h5py.File(out_path, "r") as f:
            data = f["spectrogram"][:]
            attrs = dict(f.attrs)
        return result, data, attrs

    def _chirp(self, n_samples, sr, seed=42):
        rng = np.random.default_rng(seed)
        t = np.arange(n_samples) / sr
        y = 0.5 * np.sin(2 * np.pi * (200 + 800 * t) * t) + 0.01 * rng.standard_normal(n_samples)
        return y.astype(np.float32)

    def test_matches_single_shot_reference_mono(self):
        """Chunked output is identical to single-shot STFT, with awkward sizes."""
        sr = 8000
        # Signal length and chunk size deliberately NOT multiples of the hop
        # length, so chunk boundaries land mid-frame.
        wav_path = self._write_wav(self._chirp(20_001, sr), sr)

        # Read back the quantized PCM the same way the implementation does
        y_ref, _ = sf.read(wav_path, dtype="float32")
        reference = single_shot_reference(y_ref)

        _, data, attrs = self._run_chunked(wav_path, chunk_samples=3_001)

        self.assertEqual(data.shape, reference.shape)
        self.assertTrue(np.array_equal(data, reference))
        self.assertEqual(attrs["n_frames"], len(y_ref) // HOP_LENGTH + 1)
        self.assertEqual(attrs["n_freq_bins"], N_FREQ_BINS)
        self.assertEqual(attrs["sample_rate"], sr)

    def test_chunk_size_does_not_change_output(self):
        """Different chunk sizes give byte-identical spectrograms."""
        sr = 8000
        wav_path = self._write_wav(self._chirp(10_000, sr), sr)

        _, small_chunks, _ = self._run_chunked(wav_path, chunk_samples=777)
        _, one_chunk, _ = self._run_chunked(wav_path, chunk_samples=10_000_000)

        self.assertTrue(np.array_equal(small_chunks, one_chunk))

    def test_matches_single_shot_reference_stereo(self):
        """Stereo files are downmixed to mono before the STFT."""
        sr = 8000
        y = self._chirp(9_999, sr)
        wav_path = self._write_wav(y, sr, channels=2)

        y_ref, _ = sf.read(wav_path, dtype="float32")
        reference = single_shot_reference(np.mean(y_ref, axis=1))

        _, data, _ = self._run_chunked(wav_path, chunk_samples=2_500)

        self.assertTrue(np.array_equal(data, reference))

    def test_downsampled_long_file_phase_aligned(self):
        """Files over 10 minutes are decimated consistently across chunks."""
        sr = 1000  # Low rate keeps the test fast; >10 min => 600k samples
        n_samples = 1_500_000  # 25 minutes -> downsample_factor = 3
        wav_path = self._write_wav(self._chirp(n_samples, sr), sr)

        y_ref, _ = sf.read(wav_path, dtype="float32")
        factor = int(n_samples / (10 * 60 * sr)) + 1
        self.assertEqual(factor, 3)
        reference = single_shot_reference(y_ref[::factor])

        # Chunk size not a multiple of the factor or the hop length, so
        # decimation phase must be carried across chunk boundaries.
        _, data, attrs = self._run_chunked(wav_path, chunk_samples=123_457)

        self.assertTrue(np.array_equal(data, reference))
        self.assertEqual(attrs["sample_rate"], sr / factor)
        self.assertEqual(attrs["duration"], n_samples / sr)

    def test_db_floor_is_fixed(self):
        """Silence hits the -80 dB floor the viewer's padding assumes."""
        sr = 8000
        wav_path = self._write_wav(np.zeros(5_000, dtype=np.float32), sr)

        _, data, _ = self._run_chunked(wav_path, chunk_samples=2_000)

        self.assertTrue(np.all(data == np.float16(-80.0)))
