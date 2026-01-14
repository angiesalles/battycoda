"""
Tests for Celery async tasks.

This module tests the core Celery tasks:
- calculate_audio_duration (from battycoda_app/tasks.py)
- queue_processor tasks (from battycoda_app/audio/task_modules/queue_processor.py)
- segmentation tasks (from battycoda_app/audio/task_modules/segmentation_tasks.py)
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import override_settings

from battycoda_app.models import (
    ClassificationRun,
    Classifier,
    Group,
    Project,
    Recording,
    Segmentation,
    SegmentationAlgorithm,
    Species,
)
from battycoda_app.tests.test_base import BattycodaTestCase


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class CeleryTaskTestCase(BattycodaTestCase):
    """Base class for Celery task tests. Tasks run synchronously."""

    pass


class CalculateAudioDurationTaskTests(CeleryTaskTestCase):
    """Tests for the calculate_audio_duration task."""

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

    def test_skips_recording_with_duration_and_sample_rate_set(self):
        """Test that task returns early if duration and sample_rate are already set."""
        from battycoda_app.tasks import calculate_audio_duration

        recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
            duration=10.0,
            sample_rate=44100,
        )

        result = calculate_audio_duration(recording.id)
        self.assertTrue(result)

    def test_sets_file_ready_on_processing(self):
        """Test that file_ready is set to True during processing."""
        from battycoda_app.tasks import calculate_audio_duration

        recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
            file_ready=False,
        )

        # The task will attempt to process and may retry,
        # but it should at least set file_ready=True
        try:
            calculate_audio_duration(recording.id)
        except Exception:
            pass  # Expected - no actual file

        recording.refresh_from_db()
        self.assertTrue(recording.file_ready)

    @patch("battycoda_app.tasks.calculate_audio_duration.retry")
    def test_retries_on_missing_recording(self, mock_retry):
        """Test that task retries when recording doesn't exist."""
        from battycoda_app.tasks import calculate_audio_duration

        mock_retry.side_effect = Exception("Retry called")

        with self.assertRaises(Exception) as context:
            calculate_audio_duration(999999)

        self.assertIn("Retry", str(context.exception))

    @patch("os.path.exists")
    @patch("battycoda_app.tasks.calculate_audio_duration.retry")
    def test_retries_on_missing_file(self, mock_retry, mock_exists):
        """Test that task retries when audio file doesn't exist."""
        from battycoda_app.tasks import calculate_audio_duration

        mock_exists.return_value = False
        mock_retry.side_effect = Exception("Retry called")

        recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )

        with patch.object(recording, "wav_file") as mock_wav_file:
            mock_wav_file.path = "/nonexistent/file.wav"

            with self.assertRaises(Exception) as context:
                calculate_audio_duration(recording.id)

        self.assertIn("Retry", str(context.exception))


class QueueProcessorTaskTests(CeleryTaskTestCase):
    """Tests for the queue processor tasks."""

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
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            name="Test Segmentation",
            created_by=self.user,
        )

    def test_process_classification_queue_no_queued_runs(self):
        """Test queue processor returns success when no runs are queued."""
        from battycoda_app.audio.task_modules.queue_processor import (
            process_classification_queue,
        )

        result = process_classification_queue()

        self.assertEqual(result["status"], "success")
        self.assertIn("No queued runs found", result["message"])

    @patch("battycoda_app.audio.task_modules.classification.run_classification.run_call_classification")
    def test_process_classification_queue_starts_classification(self, mock_run_classification):
        """Test queue processor starts classification for queued runs."""
        from battycoda_app.audio.task_modules.queue_processor import (
            process_classification_queue,
        )

        mock_run_classification.delay.return_value = MagicMock(id="test-task-id")

        run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            status="queued",
            created_by=self.user,
            group=self.group,
        )

        result = process_classification_queue()

        self.assertEqual(result["status"], "success")
        self.assertIn(str(run.id), result["message"])

        # Verify run status changed to pending
        run.refresh_from_db()
        self.assertEqual(run.status, "pending")

    @patch("battycoda_app.audio.task_modules.classification.dummy_classifier.run_dummy_classifier")
    def test_process_classification_queue_uses_dummy_classifier(self, mock_dummy_classifier):
        """Test queue processor uses dummy classifier when specified."""
        from battycoda_app.audio.task_modules.queue_processor import (
            process_classification_queue,
        )

        mock_dummy_classifier.delay.return_value = MagicMock(id="test-task-id")

        dummy_classifier = Classifier.objects.create(
            name="Dummy Classifier",
            response_format="highest_only",
        )

        run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            status="queued",
            created_by=self.user,
            group=self.group,
            classifier=dummy_classifier,
        )

        result = process_classification_queue()

        self.assertEqual(result["status"], "success")
        mock_dummy_classifier.delay.assert_called_once_with(run.id)

    def test_queue_classification_run_sets_status_to_queued(self):
        """Test that queue_classification_run sets the status to queued."""
        from battycoda_app.audio.task_modules.queue_processor import (
            queue_classification_run,
        )

        run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            status="pending",
            created_by=self.user,
            group=self.group,
        )

        result = queue_classification_run(run.id)

        self.assertEqual(result["status"], "success")

        run.refresh_from_db()
        self.assertEqual(run.status, "queued")

    def test_queue_classification_run_nonexistent_run(self):
        """Test that queue_classification_run handles nonexistent runs."""
        from battycoda_app.audio.task_modules.queue_processor import (
            queue_classification_run,
        )

        result = queue_classification_run(999999)

        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])

    def test_get_queue_status(self):
        """Test that get_queue_status returns correct counts."""
        from battycoda_app.audio.task_modules.queue_processor import get_queue_status

        # Create runs with different statuses
        ClassificationRun.objects.create(
            name="Queued Run 1",
            segmentation=self.segmentation,
            status="queued",
            created_by=self.user,
            group=self.group,
        )
        ClassificationRun.objects.create(
            name="Queued Run 2",
            segmentation=self.segmentation,
            status="queued",
            created_by=self.user,
            group=self.group,
        )
        ClassificationRun.objects.create(
            name="Pending Run",
            segmentation=self.segmentation,
            status="pending",
            created_by=self.user,
            group=self.group,
        )
        ClassificationRun.objects.create(
            name="In Progress Run",
            segmentation=self.segmentation,
            status="in_progress",
            created_by=self.user,
            group=self.group,
        )
        ClassificationRun.objects.create(
            name="Completed Run",
            segmentation=self.segmentation,
            status="completed",
            created_by=self.user,
            group=self.group,
        )

        result = get_queue_status()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["queue_stats"]["queued"], 2)
        self.assertEqual(result["queue_stats"]["pending"], 1)
        self.assertEqual(result["queue_stats"]["in_progress"], 1)
        self.assertEqual(result["queue_stats"]["total_waiting"], 3)


class SegmentationTaskTests(CeleryTaskTestCase):
    """Tests for the segmentation tasks."""

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
            name="Threshold Algorithm",
            algorithm_type="threshold",
        )
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            name="Test Segmentation",
            created_by=self.user,
            algorithm=self.algorithm,
            status="pending",
        )

    @patch("os.path.exists")
    def test_auto_segment_error_on_missing_file(self, mock_exists):
        """Test that segmentation returns error when WAV file is missing."""
        from battycoda_app.audio.task_modules.segmentation_tasks import (
            auto_segment_recording_task,
        )

        mock_exists.return_value = False

        result = auto_segment_recording_task(
            recording_id=self.recording.id,
            segmentation_id=self.segmentation.id,
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("WAV file not found", result["message"])

    @patch("battycoda_app.audio.utils.auto_segment_audio")
    @patch("os.path.exists")
    def test_auto_segment_creates_segments(self, mock_exists, mock_segment_audio):
        """Test that segmentation creates segments from detected onsets/offsets."""
        from battycoda_app.audio.task_modules.segmentation_tasks import (
            auto_segment_recording_task,
        )

        mock_exists.return_value = True
        mock_segment_audio.return_value = ([0.1, 0.5, 1.0], [0.3, 0.8, 1.5])

        with patch.object(self.recording, "wav_file") as mock_wav_file:
            mock_wav_file.path = "/fake/path/test.wav"

            # Need to patch the Recording.all_objects.get to return our patched recording
            with patch.object(Recording.all_objects, "get", return_value=self.recording):
                result = auto_segment_recording_task(
                    recording_id=self.recording.id,
                    segmentation_id=self.segmentation.id,
                )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["segments_created"], 3)
        self.assertEqual(result["total_segments_found"], 3)

        # Verify segmentation status was updated
        self.segmentation.refresh_from_db()
        self.assertEqual(self.segmentation.status, "completed")
        self.assertEqual(self.segmentation.progress, 100)

    @patch("battycoda_app.audio.utils.energy_based_segment_audio")
    @patch("os.path.exists")
    def test_auto_segment_uses_energy_algorithm(self, mock_exists, mock_energy_segment):
        """Test that segmentation uses energy algorithm when specified."""
        from battycoda_app.audio.task_modules.segmentation_tasks import (
            auto_segment_recording_task,
        )

        mock_exists.return_value = True
        mock_energy_segment.return_value = ([0.2, 0.6], [0.4, 0.9])

        # Create segmentation with energy algorithm
        energy_algorithm = SegmentationAlgorithm.objects.create(
            name="Energy Algorithm",
            algorithm_type="energy",
        )
        energy_segmentation = Segmentation.objects.create(
            recording=self.recording,
            name="Energy Segmentation",
            created_by=self.user,
            algorithm=energy_algorithm,
            status="pending",
        )

        with patch.object(self.recording, "wav_file") as mock_wav_file:
            mock_wav_file.path = "/fake/path/test.wav"

            with patch.object(Recording.all_objects, "get", return_value=self.recording):
                result = auto_segment_recording_task(
                    recording_id=self.recording.id,
                    segmentation_id=energy_segmentation.id,
                )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["segments_created"], 2)
        mock_energy_segment.assert_called_once()

    @patch("battycoda_app.audio.utils.auto_segment_audio")
    @patch("os.path.exists")
    def test_auto_segment_handles_algorithm_error(self, mock_exists, mock_segment_audio):
        """Test that segmentation handles errors during algorithm execution."""
        from battycoda_app.audio.task_modules.segmentation_tasks import (
            auto_segment_recording_task,
        )

        mock_exists.return_value = True
        mock_segment_audio.side_effect = Exception("Segmentation algorithm failed")

        with patch.object(self.recording, "wav_file") as mock_wav_file:
            mock_wav_file.path = "/fake/path/test.wav"

            with patch.object(Recording.all_objects, "get", return_value=self.recording):
                result = auto_segment_recording_task(
                    recording_id=self.recording.id,
                    segmentation_id=self.segmentation.id,
                )

        self.assertEqual(result["status"], "error")
        self.assertIn("Error during auto-segmentation", result["message"])


class DiskUsageTaskTests(CeleryTaskTestCase):
    """Tests for the check_disk_usage task."""

    def setUp(self):
        """Reset disk alert cooldown before each test."""
        import battycoda_app.tasks

        battycoda_app.tasks._last_disk_alert_time = None

    @patch("battycoda_app.email_utils.send_disk_usage_warning_email")
    @patch("shutil.disk_usage")
    def test_check_disk_usage_ok(self, mock_disk_usage, mock_send_email):
        """Test that disk usage check returns ok when usage is below threshold."""
        from battycoda_app.tasks import check_disk_usage

        # Mock disk usage at 50%
        mock_disk_usage.return_value = MagicMock(
            total=100 * 1024**3,  # 100 GB
            used=50 * 1024**3,  # 50 GB
            free=50 * 1024**3,  # 50 GB
        )

        result = check_disk_usage(threshold=90)

        self.assertEqual(result["status"], "ok")
        mock_send_email.assert_not_called()

    @patch("battycoda_app.email_utils.send_disk_usage_warning_email")
    @patch("shutil.disk_usage")
    def test_check_disk_usage_sends_alert(self, mock_disk_usage, mock_send_email):
        """Test that disk usage check sends alert when usage exceeds threshold."""
        from battycoda_app.tasks import check_disk_usage

        # Mock disk usage at 95%
        mock_disk_usage.return_value = MagicMock(
            total=100 * 1024**3,  # 100 GB
            used=95 * 1024**3,  # 95 GB
            free=5 * 1024**3,  # 5 GB
        )
        mock_send_email.return_value = True

        result = check_disk_usage(threshold=90)

        self.assertEqual(result["status"], "alert_sent")
        self.assertEqual(len(result["disks_over_threshold"]), 2)  # / and /home
        mock_send_email.assert_called_once()

    @patch("battycoda_app.email_utils.send_disk_usage_warning_email")
    @patch("shutil.disk_usage")
    def test_check_disk_usage_respects_cooldown(self, mock_disk_usage, mock_send_email):
        """Test that disk usage check respects alert cooldown."""
        import datetime

        import battycoda_app.tasks
        from battycoda_app.tasks import check_disk_usage

        # Set last alert time to 1 hour ago (within 4 hour cooldown)
        battycoda_app.tasks._last_disk_alert_time = datetime.datetime.now() - datetime.timedelta(hours=1)

        # Mock disk usage at 95%
        mock_disk_usage.return_value = MagicMock(
            total=100 * 1024**3,
            used=95 * 1024**3,
            free=5 * 1024**3,
        )

        result = check_disk_usage(threshold=90)

        self.assertEqual(result["status"], "alert_suppressed")
        mock_send_email.assert_not_called()


class BackupDatabaseTaskTests(CeleryTaskTestCase):
    """Tests for the backup_database_to_s3 task."""

    @patch("battycoda_app.tasks.call_command")
    def test_backup_database_success(self, mock_call_command):
        """Test successful database backup."""
        from battycoda_app.tasks import backup_database_to_s3

        result = backup_database_to_s3(bucket_name="test-bucket", prefix="test-prefix/")

        self.assertEqual(result, "Database backup completed successfully")
        mock_call_command.assert_called_once_with("backup_database", bucket="test-bucket", prefix="test-prefix/")

    @patch("battycoda_app.email_utils.send_backup_failure_email")
    @patch("battycoda_app.tasks.call_command")
    def test_backup_database_failure_retries(self, mock_call_command, mock_send_email):
        """Test that backup failure triggers retry."""
        from celery.exceptions import Retry

        from battycoda_app.tasks import backup_database_to_s3

        mock_call_command.side_effect = ValueError("Backup failed")

        # The task has max_retries=3, so the first call failure triggers a retry
        with self.assertRaises((Retry, ValueError)):
            backup_database_to_s3(bucket_name="test-bucket")
