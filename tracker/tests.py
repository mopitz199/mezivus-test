from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from tracker.models import Package


def make_package(**kwargs):
    """
    Helper that returns a saved Package with sensible defaults.
    Any keyword argument overrides the corresponding default field value,
    allowing individual tests to vary only the field they care about.
    """
    defaults = {
        "name": "Test Package",
        "tracking_code": "TRACK-001",
        "company": "Acme Corp",
    }
    defaults.update(kwargs)
    return Package.objects.create(**defaults)


class PackageCreationTests(TestCase):
    """Tests that a Package can be created and all fields are persisted correctly."""

    def test_create_package_with_valid_data_succeeds(self):
        """A Package saved with valid data is retrievable from the database."""
        package = make_package(
            name="Fragile Goods",
            tracking_code="FG-20260101",
            company="Swift Logistics",
        )

        # Re-fetch from the database to confirm persistence, not just in-memory state.
        fetched = Package.objects.get(pk=package.pk)

        self.assertEqual(fetched.name, "Fragile Goods")
        self.assertEqual(fetched.tracking_code, "FG-20260101")
        self.assertEqual(fetched.company, "Swift Logistics")

    def test_create_package_increments_database_count(self):
        """Creating a Package increases the total count in the database by one."""
        self.assertEqual(Package.objects.count(), 0)
        make_package()
        self.assertEqual(Package.objects.count(), 1)


class PackageTrackingCodeUniquenessTests(TestCase):
    """Tests that the tracking_code field enforces uniqueness at the database level."""

    def test_duplicate_tracking_code_raises_integrity_error(self):
        """
        Saving a second Package with the same tracking_code must raise IntegrityError.
        The unique constraint is enforced by the database, so the error surfaces on save().
        """
        make_package(tracking_code="DUPE-CODE")

        with self.assertRaises(IntegrityError):
            # Bypass make_package to call save() directly and observe the DB error.
            Package.objects.create(
                name="Another Package",
                tracking_code="DUPE-CODE",
                company="Other Corp",
            )

    def test_different_tracking_codes_are_both_saved(self):
        """Two packages with distinct tracking codes can coexist in the database."""
        make_package(tracking_code="UNIQUE-A")
        make_package(tracking_code="UNIQUE-B")
        self.assertEqual(Package.objects.count(), 2)


class PackageFieldMaxLengthTests(TestCase):
    """
    Tests that CharField max_length constraints are enforced via model validation.

    Django does NOT raise an error on save() for max_length violations when using
    SQLite. Validation must be triggered explicitly by calling full_clean() before
    saving. These tests confirm that the model's field definitions reject oversized
    values at the validation layer.
    """

    def _assert_field_too_long_raises_validation_error(self, field_name, max_length):
        """
        Build a Package with a value one character over the allowed max_length for
        the given field, call full_clean(), and assert a ValidationError is raised
        that specifically references that field.
        """
        oversized_value = "x" * (max_length + 1)
        package = Package(
            name="Valid Name",
            tracking_code="VALID-CODE-001",
            company="Valid Company",
        )
        # Overwrite only the field under test with the oversized value.
        setattr(package, field_name, oversized_value)

        with self.assertRaises(ValidationError) as ctx:
            package.full_clean()

        self.assertIn(field_name, ctx.exception.message_dict)

    def test_name_exceeding_max_length_fails_validation(self):
        """name longer than 200 characters fails full_clean()."""
        self._assert_field_too_long_raises_validation_error("name", max_length=200)

    def test_tracking_code_exceeding_max_length_fails_validation(self):
        """tracking_code longer than 100 characters fails full_clean()."""
        self._assert_field_too_long_raises_validation_error("tracking_code", max_length=100)

    def test_company_exceeding_max_length_fails_validation(self):
        """company longer than 100 characters fails full_clean()."""
        self._assert_field_too_long_raises_validation_error("company", max_length=100)

    def test_name_at_exact_max_length_passes_validation(self):
        """A name of exactly 200 characters is on the boundary and must be valid."""
        package = Package(
            name="y" * 200,
            tracking_code="BOUNDARY-001",
            company="Valid Company",
        )
        # full_clean() must not raise for a value at the exact limit.
        try:
            package.full_clean()
        except ValidationError as exc:
            if "name" in exc.message_dict:
                self.fail(
                    "full_clean() raised ValidationError for name at max_length=200."
                )

    def test_tracking_code_at_exact_max_length_passes_validation(self):
        """A tracking_code of exactly 100 characters is valid."""
        package = Package(
            name="Valid Name",
            tracking_code="t" * 100,
            company="Valid Company",
        )
        try:
            package.full_clean()
        except ValidationError as exc:
            if "tracking_code" in exc.message_dict:
                self.fail(
                    "full_clean() raised ValidationError for tracking_code at max_length=100."
                )

    def test_company_at_exact_max_length_passes_validation(self):
        """A company of exactly 100 characters is valid."""
        package = Package(
            name="Valid Name",
            tracking_code="BOUNDARY-002",
            company="c" * 100,
        )
        try:
            package.full_clean()
        except ValidationError as exc:
            if "company" in exc.message_dict:
                self.fail(
                    "full_clean() raised ValidationError for company at max_length=100."
                )


class PackageTimestampTests(TestCase):
    """Tests for the auto-managed created_at and updated_at timestamp fields."""

    def test_created_at_is_set_automatically_on_creation(self):
        """created_at must be non-None and timezone-aware after the first save."""
        package = make_package()

        self.assertIsNotNone(package.created_at)
        # USE_TZ = True in settings, so the value must carry timezone information.
        self.assertIsNotNone(package.created_at.tzinfo)

    def test_updated_at_is_set_automatically_on_creation(self):
        """updated_at must also be populated on initial save, not left as None."""
        package = make_package()

        self.assertIsNotNone(package.updated_at)

    def test_created_at_is_approximately_now_on_creation(self):
        """
        created_at should be very close to the current time at the moment of save.
        A tolerance of two seconds accommodates any test-runner latency without
        requiring time-mocking for this simple sanity check.
        """
        before = timezone.now()
        package = make_package()
        after = timezone.now()

        self.assertGreaterEqual(package.created_at, before)
        self.assertLessEqual(package.created_at, after)

    def test_updated_at_changes_after_save_but_created_at_does_not(self):
        """
        After modifying a Package and calling save(), updated_at must advance
        while created_at must remain exactly the same value it had at creation.

        auto_now_add=True pins created_at to the first insert and never touches it
        again. auto_now=True rewrites updated_at on every save().
        """
        package = make_package()

        original_created_at = package.created_at
        original_updated_at = package.updated_at

        # Move time forward so that updated_at gets a strictly later timestamp.
        # We re-fetch after save() because auto_now updates the DB column but
        # Django also refreshes the in-memory instance's field via update_fields
        # only when save(update_fields=...) is used. A fresh DB fetch is the
        # safest way to read the authoritative persisted value.
        import time
        time.sleep(0.05)  # 50 ms — enough for the timestamp to differ on all OSes.

        package.name = "Updated Package Name"
        package.save()

        package.refresh_from_db()

        self.assertEqual(
            package.created_at,
            original_created_at,
            "created_at must not change after an update.",
        )
        self.assertGreater(
            package.updated_at,
            original_updated_at,
            "updated_at must be strictly later than its value before the update.",
        )


class DatabaseHealthViewTests(TestCase):
    """Tests for the database health-check endpoint."""

    def test_database_health_returns_ok_when_connection_works(self):
        """The endpoint should return HTTP 200 when a simple DB query succeeds."""
        response = self.client.get("/health/db/")

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"database": "ok"})

    @patch("tracker.views.connection.cursor", side_effect=Exception("database unavailable"))
    def test_database_health_returns_error_when_query_fails(self, _mock_cursor):
        """The endpoint should return HTTP 500 when opening a DB cursor fails."""
        response = self.client.get("/health/db/")

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            response.content,
            {"database": "error", "detail": "database unavailable"},
        )
