"""
Tests for core models: Recording, Segmentation, Classification, and Notification models.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from battycoda_app.models import (
    Call,
    CallProbability,
    ClassificationResult,
    ClassificationRun,
    Classifier,
    ClassifierTrainingJob,
    Group,
    Project,
    Recording,
    Segment,
    Segmentation,
    SegmentationAlgorithm,
    Species,
)
from battycoda_app.models.notification import UserNotification
from battycoda_app.tests.test_base import BattycodaTestCase


class RecordingModelTests(BattycodaTestCase):
    """Tests for the Recording model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )

    def test_str_representation(self):
        """Test that the string representation returns the recording name."""
        recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )
        self.assertEqual(str(recording), "Test Recording")

    def test_default_manager_excludes_hidden(self):
        """Test that the default manager excludes hidden recordings."""
        visible = Recording.all_objects.create(
            name="Visible Recording",
            hidden=False,
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )
        hidden = Recording.all_objects.create(
            name="Hidden Recording",
            hidden=True,
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )

        # Default manager should only return visible recordings
        self.assertIn(visible, Recording.objects.all())
        self.assertNotIn(hidden, Recording.objects.all())

    def test_all_objects_manager_includes_hidden(self):
        """Test that the all_objects manager includes hidden recordings."""
        hidden = Recording.all_objects.create(
            name="Hidden Recording",
            hidden=True,
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )

        # all_objects should include hidden recordings
        self.assertIn(hidden, Recording.all_objects.all())

    def test_get_segments_sorted_by_onset(self):
        """Test that get_segments returns segments sorted by onset time."""
        recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )
        segmentation = Segmentation.objects.create(
            recording=recording,
            name="Test Segmentation",
            created_by=self.user,
        )

        # Create segments out of order
        seg2 = Segment.objects.create(
            recording=recording,
            segmentation=segmentation,
            onset=2.0,
            offset=3.0,
            created_by=self.user,
        )
        seg1 = Segment.objects.create(
            recording=recording,
            segmentation=segmentation,
            onset=0.5,
            offset=1.0,
            created_by=self.user,
        )
        seg3 = Segment.objects.create(
            recording=recording,
            segmentation=segmentation,
            onset=1.5,
            offset=2.0,
            created_by=self.user,
        )

        # get_segments should return in onset order
        segments = list(recording.get_segments())
        self.assertEqual(segments[0], seg1)
        self.assertEqual(segments[1], seg3)
        self.assertEqual(segments[2], seg2)

    def test_meta_options(self):
        """Test that Recording model has correct meta options."""
        self.assertEqual(Recording._meta.ordering, ["-created_at"])
        self.assertEqual(Recording._meta.verbose_name, "Recording")
        self.assertEqual(Recording._meta.verbose_name_plural, "Recordings")


class SegmentationAlgorithmModelTests(BattycodaTestCase):
    """Tests for the SegmentationAlgorithm model."""

    def test_str_representation(self):
        """Test that the string representation returns the algorithm name."""
        algorithm = SegmentationAlgorithm.objects.create(
            name="Threshold Algorithm",
            algorithm_type="threshold",
        )
        self.assertEqual(str(algorithm), "Threshold Algorithm")

    def test_algorithm_type_choices(self):
        """Test that all algorithm type choices are valid."""
        valid_types = ["threshold", "energy", "ml", "external"]
        for alg_type in valid_types:
            algorithm = SegmentationAlgorithm.objects.create(
                name=f"Test {alg_type}",
                algorithm_type=alg_type,
            )
            self.assertEqual(algorithm.algorithm_type, alg_type)

    def test_meta_options(self):
        """Test that SegmentationAlgorithm model has correct meta options."""
        self.assertEqual(SegmentationAlgorithm._meta.ordering, ["name"])


class SegmentationModelTests(BattycodaTestCase):
    """Tests for the Segmentation model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )
        self.recording = Recording.all_objects.create(
            name="Test Recording",
            species=self.species,
            project=self.project,
            group=self.group,
            created_by=self.user,
        )

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        segmentation = Segmentation.objects.create(
            recording=self.recording,
            name="Test Segmentation",
            status="completed",
            created_by=self.user,
        )
        expected = f"Segmentation job {segmentation.id} - Test Recording (completed)"
        self.assertEqual(str(segmentation), expected)

    def test_is_processing_property_pending(self):
        """Test that is_processing returns True for pending status."""
        segmentation = Segmentation.objects.create(
            recording=self.recording,
            status="pending",
            created_by=self.user,
        )
        self.assertTrue(segmentation.is_processing)

    def test_is_processing_property_in_progress(self):
        """Test that is_processing returns True for in_progress status."""
        segmentation = Segmentation.objects.create(
            recording=self.recording,
            status="in_progress",
            created_by=self.user,
        )
        self.assertTrue(segmentation.is_processing)

    def test_is_processing_property_completed(self):
        """Test that is_processing returns False for completed status."""
        segmentation = Segmentation.objects.create(
            recording=self.recording,
            status="completed",
            created_by=self.user,
        )
        self.assertFalse(segmentation.is_processing)

    def test_is_processing_property_failed(self):
        """Test that is_processing returns False for failed status."""
        segmentation = Segmentation.objects.create(
            recording=self.recording,
            status="failed",
            created_by=self.user,
        )
        self.assertFalse(segmentation.is_processing)

    def test_status_choices(self):
        """Test that all status choices are valid."""
        valid_statuses = ["pending", "in_progress", "completed", "failed"]
        for status in valid_statuses:
            segmentation = Segmentation.objects.create(
                recording=self.recording,
                status=status,
                created_by=self.user,
            )
            self.assertEqual(segmentation.status, status)

    def test_meta_options(self):
        """Test that Segmentation model has correct meta options."""
        self.assertEqual(Segmentation._meta.ordering, ["-created_at"])


class SegmentModelTests(BattycodaTestCase):
    """Tests for the Segment model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
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

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=2.5,
            created_by=self.user,
        )
        self.assertEqual(str(segment), "Test Recording (1.00s - 2.50s)")

    def test_duration_property(self):
        """Test that the duration property calculates correctly."""
        segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=3.5,
            created_by=self.user,
        )
        self.assertEqual(segment.duration, 2.5)

    def test_duration_ms_property(self):
        """Test that the duration_ms property calculates correctly."""
        segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=3.5,
            created_by=self.user,
        )
        self.assertEqual(segment.duration_ms, 2500)

    def test_to_dict_method(self):
        """Test that to_dict returns correct dictionary representation."""
        segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            name="Test Segment",
            onset=1.0,
            offset=2.0,
            notes="Some notes",
            created_by=self.user,
        )
        result = segment.to_dict()

        self.assertEqual(result["id"], segment.id)
        self.assertEqual(result["name"], "Test Segment")
        self.assertEqual(result["onset"], 1.0)
        self.assertEqual(result["offset"], 2.0)
        self.assertEqual(result["duration"], 1.0)
        self.assertEqual(result["notes"], "Some notes")

    def test_to_dict_without_name_uses_default(self):
        """Test that to_dict uses default name when name is None."""
        segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=2.0,
            created_by=self.user,
        )
        result = segment.to_dict()
        self.assertEqual(result["name"], f"Segment {segment.id}")

    def test_segment_requires_segmentation(self):
        """Test that creating a segment without segmentation raises error."""
        segment = Segment(
            recording=self.recording,
            onset=1.0,
            offset=2.0,
            created_by=self.user,
        )
        with self.assertRaises(ValueError) as context:
            segment.save()
        self.assertIn("explicitly assigned to a segmentation", str(context.exception))

    def test_save_marks_segmentation_as_manually_edited(self):
        """Test that saving a segment marks its segmentation as manually edited."""
        self.assertFalse(self.segmentation.manually_edited)

        Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=2.0,
            created_by=self.user,
        )

        self.segmentation.refresh_from_db()
        self.assertTrue(self.segmentation.manually_edited)

    def test_meta_options(self):
        """Test that Segment model has correct meta options."""
        self.assertEqual(Segment._meta.ordering, ["onset"])


class ClassifierModelTests(BattycodaTestCase):
    """Tests for the Classifier model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.species2 = Species.objects.create(
            name="Another Species", description="Another species", created_by=self.user, group=self.group
        )

    def test_str_representation(self):
        """Test that the string representation returns the classifier name."""
        classifier = Classifier.objects.create(
            name="Test Classifier",
            response_format="highest_only",
        )
        self.assertEqual(str(classifier), "Test Classifier")

    def test_species_immutability(self):
        """Test that species cannot be changed after initial assignment."""
        classifier = Classifier.objects.create(
            name="Test Classifier",
            response_format="highest_only",
            species=self.species,
        )

        # Try to change species
        classifier.species = self.species2
        with self.assertRaises(ValidationError) as context:
            classifier.save()

        self.assertIn("species", context.exception.message_dict)
        self.assertIn("Cannot change the species", str(context.exception))

    def test_species_can_be_set_initially(self):
        """Test that species can be set on initial creation."""
        classifier = Classifier.objects.create(
            name="Test Classifier",
            response_format="highest_only",
            species=self.species,
        )
        self.assertEqual(classifier.species, self.species)

    def test_species_can_be_added_to_classifier_without_species(self):
        """Test that species can be set if it was initially null."""
        classifier = Classifier.objects.create(
            name="Test Classifier",
            response_format="highest_only",
            species=None,
        )

        # Setting species for the first time should work
        classifier.species = self.species
        classifier.save()

        classifier.refresh_from_db()
        self.assertEqual(classifier.species, self.species)

    def test_response_format_choices(self):
        """Test that all response format choices are valid."""
        valid_formats = ["full_probability", "highest_only"]
        for fmt in valid_formats:
            classifier = Classifier.objects.create(
                name=f"Test {fmt}",
                response_format=fmt,
            )
            self.assertEqual(classifier.response_format, fmt)

    def test_meta_options(self):
        """Test that Classifier model has correct meta options."""
        self.assertEqual(Classifier._meta.ordering, ["name"])


class ClassificationRunModelTests(BattycodaTestCase):
    """Tests for the ClassificationRun model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
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

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(str(run), "Test Run - Test Recording")

    def test_status_choices(self):
        """Test that all status choices are valid."""
        valid_statuses = ["queued", "pending", "in_progress", "completed", "failed"]
        for status in valid_statuses:
            run = ClassificationRun.objects.create(
                name=f"Test {status}",
                segmentation=self.segmentation,
                status=status,
                created_by=self.user,
                group=self.group,
            )
            self.assertEqual(run.status, status)

    def test_progress_default(self):
        """Test that progress defaults to 0."""
        run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(run.progress, 0.0)

    def test_meta_options(self):
        """Test that ClassificationRun model has correct meta options."""
        self.assertEqual(ClassificationRun._meta.ordering, ["-created_at"])


class ClassificationResultModelTests(BattycodaTestCase):
    """Tests for the ClassificationResult model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
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
        self.segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=2.0,
            created_by=self.user,
        )
        self.classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            created_by=self.user,
            group=self.group,
        )

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        result = ClassificationResult.objects.create(
            classification_run=self.classification_run,
            segment=self.segment,
        )
        self.assertEqual(str(result), f"Classification for {self.segment}")

    def test_meta_options(self):
        """Test that ClassificationResult model has correct meta options."""
        self.assertEqual(ClassificationResult._meta.ordering, ["segment__onset"])


class CallProbabilityModelTests(BattycodaTestCase):
    """Tests for the CallProbability model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.call = Call.objects.create(
            species=self.species,
            short_name="TC",
            long_name="Test Call",
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
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
        self.segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=1.0,
            offset=2.0,
            created_by=self.user,
        )
        self.classification_run = ClassificationRun.objects.create(
            name="Test Run",
            segmentation=self.segmentation,
            created_by=self.user,
            group=self.group,
        )
        self.classification_result = ClassificationResult.objects.create(
            classification_run=self.classification_run,
            segment=self.segment,
        )

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        prob = CallProbability.objects.create(
            classification_result=self.classification_result,
            call=self.call,
            probability=0.85,
        )
        self.assertEqual(str(prob), "TC: 0.85")

    def test_meta_options(self):
        """Test that CallProbability model has correct meta options."""
        self.assertEqual(CallProbability._meta.ordering, ["-probability"])


class ClassifierTrainingJobModelTests(BattycodaTestCase):
    """Tests for the ClassifierTrainingJob model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.group = Group.objects.create(name="Test Group", description="A test group")

    def test_str_representation_without_task_batch(self):
        """Test string representation when task_batch is None."""
        job = ClassifierTrainingJob.objects.create(
            name="Test Training Job",
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(str(job), "Test Training Job")

    def test_status_choices(self):
        """Test that all status choices are valid."""
        valid_statuses = ["pending", "in_progress", "completed", "failed"]
        for status in valid_statuses:
            job = ClassifierTrainingJob.objects.create(
                name=f"Test {status}",
                status=status,
                created_by=self.user,
                group=self.group,
            )
            self.assertEqual(job.status, status)

    def test_meta_options(self):
        """Test that ClassifierTrainingJob model has correct meta options."""
        self.assertEqual(ClassifierTrainingJob._meta.ordering, ["-created_at"])


class UserNotificationModelTests(BattycodaTestCase):
    """Tests for the UserNotification model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

    def test_str_representation(self):
        """Test that the string representation returns expected format."""
        notif = UserNotification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            notification_type="info",
        )
        self.assertEqual(str(notif), "Information: Test Notification (testuser)")

    def test_notification_type_choices(self):
        """Test that all notification type choices are valid."""
        valid_types = ["segmentation", "classification", "training", "system", "info"]
        for notif_type in valid_types:
            notif = UserNotification.objects.create(
                user=self.user,
                title=f"Test {notif_type}",
                message="Test message",
                notification_type=notif_type,
            )
            self.assertEqual(notif.notification_type, notif_type)

    def test_icon_choices(self):
        """Test that all icon choices are valid."""
        valid_icons = ["s7-check", "s7-close", "s7-info", "s7-attention", "s7-bell"]
        for icon in valid_icons:
            notif = UserNotification.objects.create(
                user=self.user,
                title=f"Test {icon}",
                message="Test message",
                icon=icon,
            )
            self.assertEqual(notif.icon, icon)

    def test_default_is_read_false(self):
        """Test that notifications are unread by default."""
        notif = UserNotification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
        )
        self.assertFalse(notif.is_read)

    def test_mark_as_read(self):
        """Test that notification can be marked as read."""
        notif = UserNotification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            is_read=False,
        )

        notif.is_read = True
        notif.save()

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_unread_count_query(self):
        """Test querying unread notification count."""
        # Clear any existing notifications from signals
        UserNotification.objects.filter(user=self.user).delete()

        # Create 3 unread and 2 read notifications
        for i in range(3):
            UserNotification.objects.create(
                user=self.user,
                title=f"Unread {i}",
                message="Test message",
                is_read=False,
            )
        for i in range(2):
            UserNotification.objects.create(
                user=self.user,
                title=f"Read {i}",
                message="Test message",
                is_read=True,
            )

        unread_count = UserNotification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread_count, 3)

    def test_add_notification_classmethod(self):
        """Test the add_notification class method."""
        notif = UserNotification.add_notification(
            user=self.user,
            title="Test Title",
            message="Test Message",
            notification_type="system",
            icon="s7-info",
            link="/test/link/",
        )

        self.assertEqual(notif.user, self.user)
        self.assertEqual(notif.title, "Test Title")
        self.assertEqual(notif.message, "Test Message")
        self.assertEqual(notif.notification_type, "system")
        self.assertEqual(notif.icon, "s7-info")
        self.assertEqual(notif.link, "/test/link/")
        self.assertFalse(notif.is_read)

    def test_meta_options(self):
        """Test that UserNotification model has correct meta options."""
        self.assertEqual(UserNotification._meta.ordering, ["-created_at"])
