"""
Tests for the classification module.

Tests cover:
- r_server_client: R server communication and batch processing
- result_processing: Feature file combining and result saving
- run_classification: Main classification task orchestration
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import override_settings

from battycoda_app.models import (
    Call,
    ClassificationRun,
    Classifier,
    Group,
    Project,
    Recording,
    Segment,
    Segmentation,
    SegmentationAlgorithm,
    Species,
)
from battycoda_app.tests.test_base import BattycodaTestCase


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ClassificationTestCase(BattycodaTestCase):
    """Base class for classification tests. Tasks run synchronously."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species",
            description="A test species",
            created_by=self.user,
            group=self.group,
        )
        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            created_by=self.user,
            group=self.group,
        )
        self.recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )
        self.algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="threshold",
        )
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            name="Test Segmentation",
            created_by=self.user,
            algorithm=self.algorithm,
            status="completed",
        )
        # Create some test segments
        self.segment1 = Segment.objects.create(
            segmentation=self.segmentation,
            recording=self.recording,
            onset=0.1,
            offset=0.3,
            created_by=self.user,
        )
        self.segment2 = Segment.objects.create(
            segmentation=self.segmentation,
            recording=self.recording,
            onset=0.5,
            offset=0.8,
            created_by=self.user,
        )
        # Create call types for the species
        self.call1 = Call.objects.create(
            species=self.species,
            short_name="call_a",
            long_name="Call Type A",
        )
        self.call2 = Call.objects.create(
            species=self.species,
            short_name="call_b",
            long_name="Call Type B",
        )


class ResultProcessingTests(ClassificationTestCase):
    """Tests for result_processing module."""

    def test_save_batch_results_creates_results(self):
        """Test that save_batch_results creates ClassificationResult and CallProbability records."""
        from battycoda_app.audio.task_modules.classification.result_processing import save_batch_results
        from battycoda_app.models.classification import CallProbability, ClassificationResult

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )
        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=classifier,
            status="in_progress",
            created_by=self.user,
            group=self.group,
        )

        # Simulate batch results from R server
        batch_results = [
            (
                self.segment1.id,
                {"class_probabilities": {"call_a": 80.0, "call_b": 20.0}},
                {"segment_id": self.segment1.id},
            ),
            (
                self.segment2.id,
                {"class_probabilities": {"call_a": 30.0, "call_b": 70.0}},
                {"segment_id": self.segment2.id},
            ),
        ]

        segments = Segment.objects.filter(segmentation=self.segmentation)
        calls = Call.objects.filter(species=self.species)

        saved_count = save_batch_results(batch_results, classification_run, segments, calls)

        self.assertEqual(saved_count, 2)
        self.assertEqual(ClassificationResult.objects.filter(classification_run=classification_run).count(), 2)
        self.assertEqual(
            CallProbability.objects.filter(classification_result__classification_run=classification_run).count(), 4
        )

        # Verify probabilities were normalized correctly (divided by 100)
        result1 = ClassificationResult.objects.get(segment=self.segment1)
        prob_a = CallProbability.objects.get(classification_result=result1, call=self.call1)
        self.assertAlmostEqual(prob_a.probability, 0.8, places=2)

    def test_save_batch_results_handles_missing_probabilities(self):
        """Test that save_batch_results handles missing call probabilities gracefully."""
        from battycoda_app.audio.task_modules.classification.result_processing import save_batch_results
        from battycoda_app.models.classification import CallProbability, ClassificationResult

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )
        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=classifier,
            status="in_progress",
            created_by=self.user,
            group=self.group,
        )

        # Simulate batch results with missing call_b probability
        batch_results = [
            (
                self.segment1.id,
                {"class_probabilities": {"call_a": 100.0}},  # Missing call_b
                {"segment_id": self.segment1.id},
            ),
        ]

        segments = Segment.objects.filter(segmentation=self.segmentation)
        calls = Call.objects.filter(species=self.species)

        saved_count = save_batch_results(batch_results, classification_run, segments, calls)

        self.assertEqual(saved_count, 1)

        # Check that missing probability defaults to 0
        result = ClassificationResult.objects.get(segment=self.segment1)
        prob_b = CallProbability.objects.get(classification_result=result, call=self.call2)
        self.assertEqual(prob_b.probability, 0.0)

    def test_combine_features_files_returns_none_for_empty_list(self):
        """Test that combine_features_files returns None when no files provided."""
        from battycoda_app.audio.task_modules.classification.result_processing import combine_features_files

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )
        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=classifier,
            status="in_progress",
            created_by=self.user,
            group=self.group,
        )

        result = combine_features_files([], {}, classification_run)
        self.assertIsNone(result)

    @patch("battycoda_app.audio.task_modules.classification.result_processing.get_local_tmp")
    def test_combine_features_files_combines_csvs(self, mock_get_tmp):
        """Test that combine_features_files properly combines multiple CSV files."""
        from battycoda_app.audio.task_modules.classification.result_processing import combine_features_files

        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_get_tmp.return_value = tmp_dir

            # Create test CSV files
            csv1_path = os.path.join(tmp_dir, "batch_0_features.csv")
            csv2_path = os.path.join(tmp_dir, "batch_1_features.csv")

            with open(csv1_path, "w") as f:
                f.write("sound.files,selec,feature1\n")
                f.write("segment_1.wav,1,0.5\n")

            with open(csv2_path, "w") as f:
                f.write("sound.files,selec,feature1\n")
                f.write("segment_2.wav,1,0.7\n")

            classifier = Classifier.objects.create(
                name="Test Classifier",
                service_url="http://localhost:8001",
                endpoint="/predict/knn",
            )
            classification_run = ClassificationRun.objects.create(
                name="Test Run",
                segmentation=self.segmentation,
                classifier=classifier,
                status="in_progress",
                created_by=self.user,
                group=self.group,
            )

            segment_metadata = {
                "segment_1.wav": {
                    "segment_id": 1,
                    "task_id": None,
                    "start_time": 0.1,
                    "end_time": 0.3,
                    "recording_name": "Test Recording",
                    "wav_filename": "test.wav",
                },
                "segment_2.wav": {
                    "segment_id": 2,
                    "task_id": None,
                    "start_time": 0.5,
                    "end_time": 0.8,
                    "recording_name": "Test Recording",
                    "wav_filename": "test.wav",
                },
            }

            result_path = combine_features_files([csv1_path, csv2_path], segment_metadata, classification_run)

            self.assertIsNotNone(result_path)
            self.assertTrue(os.path.exists(result_path))

            # Verify the combined file has both rows plus enhanced columns
            import pandas as pd

            df = pd.read_csv(result_path)
            self.assertEqual(len(df), 2)
            self.assertIn("task_id", df.columns)
            self.assertIn("call_start_time", df.columns)
            self.assertIn("recording_name", df.columns)


class RServerClientTests(ClassificationTestCase):
    """Tests for r_server_client module."""

    @patch("battycoda_app.audio.task_modules.classification.r_server_client.requests.post")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.extract_audio_segment")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.sf.write")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.get_local_tmp")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.get_r_server_path")
    def test_process_classification_batch_success(
        self, mock_r_path, mock_get_tmp, mock_sf_write, mock_extract, mock_post
    ):
        """Test successful batch processing."""
        from battycoda_app.audio.task_modules.classification.r_server_client import process_classification_batch

        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_get_tmp.return_value = tmp_dir
            mock_r_path.side_effect = lambda x: x  # Return path unchanged
            mock_extract.return_value = ([0.1, 0.2, 0.3], 44100)  # Fake audio data

            # Mock R server response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "file_results": {
                    f"segment_{self.segment1.id}.wav": {"class_probabilities": {"call_a": [80.0], "call_b": [20.0]}},
                },
            }
            mock_post.return_value = mock_response

            classifier = Classifier.objects.create(
                name="Test Classifier",
                service_url="http://localhost:8001",
                endpoint="/predict/knn",
            )
            classification_run = ClassificationRun.objects.create(
                name="Test Run",
                segmentation=self.segmentation,
                classifier=classifier,
                status="in_progress",
                created_by=self.user,
                group=self.group,
            )

            # Set up recording with a mock wav_file
            with patch.object(self.recording, "wav_file") as mock_wav_file:
                mock_wav_file.path = "/fake/path/test.wav"
                mock_wav_file.name = "test.wav"

                batch_results, segment_map, features_file = process_classification_batch(
                    batch_index=0,
                    batch_segments=[self.segment1],
                    classification_run=classification_run,
                    recording=self.recording,
                    classifier=classifier,
                    service_url="http://localhost:8001",
                    endpoint="http://localhost:8001/predict/knn",
                    model_path_for_r_server="/path/to/model.RData",
                    segment_list_start_idx=0,
                )

            self.assertEqual(len(batch_results), 1)
            self.assertEqual(batch_results[0][0], self.segment1.id)
            self.assertIn(f"segment_{self.segment1.id}.wav", segment_map)

    @patch("battycoda_app.audio.task_modules.classification.r_server_client.requests.post")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.extract_audio_segment")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.sf.write")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.get_local_tmp")
    @patch("battycoda_app.audio.task_modules.classification.r_server_client.get_r_server_path")
    def test_process_classification_batch_handles_r_server_error(
        self, mock_r_path, mock_get_tmp, mock_sf_write, mock_extract, mock_post
    ):
        """Test that batch processing raises error on R server failure."""
        from battycoda_app.audio.task_modules.classification.r_server_client import process_classification_batch

        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_get_tmp.return_value = tmp_dir
            mock_r_path.side_effect = lambda x: x
            mock_extract.return_value = ([0.1, 0.2, 0.3], 44100)

            # Mock R server error response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_post.return_value = mock_response

            classifier = Classifier.objects.create(
                name="Test Classifier",
                service_url="http://localhost:8001",
                endpoint="/predict/knn",
            )
            classification_run = ClassificationRun.objects.create(
                name="Test Run",
                segmentation=self.segmentation,
                classifier=classifier,
                status="in_progress",
                created_by=self.user,
                group=self.group,
            )

            with patch.object(self.recording, "wav_file") as mock_wav_file:
                mock_wav_file.path = "/fake/path/test.wav"
                mock_wav_file.name = "test.wav"

                with self.assertRaises(RuntimeError) as context:
                    process_classification_batch(
                        batch_index=0,
                        batch_segments=[self.segment1],
                        classification_run=classification_run,
                        recording=self.recording,
                        classifier=classifier,
                        service_url="http://localhost:8001",
                        endpoint="http://localhost:8001/predict/knn",
                        model_path_for_r_server="/path/to/model.RData",
                        segment_list_start_idx=0,
                    )

            self.assertIn("Classifier service error", str(context.exception))


class RunClassificationTests(ClassificationTestCase):
    """Tests for the main run_classification task."""

    def test_run_classification_fails_without_classifier(self):
        """Test that classification fails when no classifier is specified and no default exists."""
        from battycoda_app.audio.task_modules.classification.run_classification import run_call_classification

        # Delete any existing default classifiers
        Classifier.objects.filter(name__in=["KNN E. fuscus", "R-direct Classifier"]).delete()

        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=None,
            status="queued",
            created_by=self.user,
            group=self.group,
        )

        result = run_call_classification(classification_run.id)

        self.assertEqual(result["status"], "error")
        self.assertIn("No classifier specified", result["message"])

        classification_run.refresh_from_db()
        self.assertEqual(classification_run.status, "failed")

    @patch("battycoda_app.audio.task_modules.classification.run_classification.run_dummy_classifier")
    def test_run_classification_uses_dummy_classifier(self, mock_dummy):
        """Test that dummy classifier is used when specified."""
        from battycoda_app.audio.task_modules.classification.run_classification import run_call_classification

        mock_dummy.return_value = {"status": "success", "message": "Dummy classification complete"}

        dummy_classifier = Classifier.objects.create(
            name="Dummy Classifier",
            response_format="highest_only",
        )
        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=dummy_classifier,
            status="queued",
            created_by=self.user,
            group=self.group,
        )

        result = run_call_classification(classification_run.id)

        self.assertEqual(result["status"], "success")
        mock_dummy.assert_called_once()

    @patch("battycoda_app.audio.task_modules.classification.run_classification.check_r_server_connection")
    @patch("os.path.exists")
    def test_run_classification_fails_on_missing_wav_file(self, mock_exists, mock_check_r):
        """Test that classification fails when WAV file doesn't exist."""
        from battycoda_app.audio.task_modules.classification.run_classification import run_call_classification

        mock_exists.return_value = False
        mock_check_r.return_value = (True, None)

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )
        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=classifier,
            status="queued",
            created_by=self.user,
            group=self.group,
        )

        with patch.object(self.recording, "wav_file") as mock_wav_file:
            mock_wav_file.path = "/nonexistent/file.wav"
            mock_wav_file.__bool__ = lambda x: True

            result = run_call_classification(classification_run.id)

        self.assertEqual(result["status"], "error")
        self.assertIn("WAV file not found", result["message"])

    @patch("battycoda_app.audio.task_modules.classification.run_classification._validate_classification_prerequisites")
    def test_run_classification_fails_on_r_server_down(self, mock_validate):
        """Test that classification fails when R server is not available."""
        from battycoda_app.audio.task_modules.classification.run_classification import run_call_classification

        # Mock validation to return R server error (bypasses wav file check)
        mock_validate.return_value = "R server not responding"

        classifier = Classifier.objects.create(
            name="Test Classifier R Down",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )

        classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            classifier=classifier,
            status="queued",
            created_by=self.user,
            group=self.group,
        )

        result = run_call_classification(classification_run.id)

        self.assertEqual(result["status"], "error")
        self.assertIn("R server not responding", result["message"])

    def test_get_default_classifier_returns_none_when_not_found(self):
        """Test that _get_default_classifier returns None when no defaults exist."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_default_classifier

        # Delete any existing default classifiers
        Classifier.objects.filter(name__in=["KNN E. fuscus", "R-direct Classifier"]).delete()

        result = _get_default_classifier(Classifier)
        self.assertIsNone(result)

    def test_get_default_classifier_returns_knn_first(self):
        """Test that _get_default_classifier prefers KNN E. fuscus."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_default_classifier

        # Delete any existing default classifiers first
        Classifier.objects.filter(name__in=["KNN E. fuscus", "R-direct Classifier"]).delete()

        knn_classifier = Classifier.objects.create(
            name="KNN E. fuscus",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
        )
        Classifier.objects.create(
            name="R-direct Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/lda",
        )

        result = _get_default_classifier(Classifier)
        self.assertEqual(result.id, knn_classifier.id)

    def test_get_default_classifier_falls_back_to_r_direct(self):
        """Test that _get_default_classifier falls back to R-direct Classifier."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_default_classifier

        # Delete any existing default classifiers first
        Classifier.objects.filter(name__in=["KNN E. fuscus", "R-direct Classifier"]).delete()

        r_direct = Classifier.objects.create(
            name="R-direct Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/lda",
        )

        result = _get_default_classifier(Classifier)
        self.assertEqual(result.id, r_direct.id)


class ClassificationUtilsTests(ClassificationTestCase):
    """Tests for classification utility functions."""

    def test_get_model_path_returns_none_for_no_model(self):
        """Test that _get_model_path returns None when classifier has no model file."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_model_path

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
            model_file="",
        )

        result = _get_model_path(classifier)
        self.assertIsNone(result)

    @patch("battycoda_app.audio.task_modules.classification.run_classification.get_r_server_path")
    @patch("os.path.exists")
    def test_get_model_path_returns_r_server_path(self, mock_exists, mock_r_path):
        """Test that _get_model_path returns the R server formatted path."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_model_path

        mock_exists.return_value = True
        mock_r_path.return_value = "/r_server/path/to/model.RData"

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
            model_file="data/models/test_model.RData",
        )

        result = _get_model_path(classifier)
        self.assertEqual(result, "/r_server/path/to/model.RData")

    @patch("os.path.exists")
    def test_get_model_path_raises_on_missing_file(self, mock_exists):
        """Test that _get_model_path raises ValueError when model file doesn't exist."""
        from battycoda_app.audio.task_modules.classification.run_classification import _get_model_path

        mock_exists.return_value = False

        classifier = Classifier.objects.create(
            name="Test Classifier",
            service_url="http://localhost:8001",
            endpoint="/predict/knn",
            model_file="data/models/nonexistent.RData",
        )

        with self.assertRaises(ValueError) as context:
            _get_model_path(classifier)

        self.assertIn("Model file not found", str(context.exception))
