"""
Custom test runner that defaults to --keepdb for faster repeat runs.

Uses a migration fingerprint to automatically recreate the DB when migrations change.
Override with: python manage.py test --no-keepdb
"""

import hashlib
import os

from django.conf import settings
from django.test.runner import DiscoverRunner

FINGERPRINT_FILE = os.path.join(settings.BASE_DIR, ".test_db_fingerprint")


def _migration_fingerprint():
    """Hash all migration file paths + mtimes to detect changes."""
    import importlib
    import pkgutil

    hasher = hashlib.sha256()

    for app_config in sorted(settings.INSTALLED_APPS):
        module_name = f"{app_config}.migrations"
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            continue

        if not hasattr(mod, "__path__"):
            continue

        for _importer, name, _ispkg in sorted(pkgutil.iter_modules(mod.__path__)):
            fpath = os.path.join(mod.__path__[0], f"{name}.py")
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                hasher.update(f"{fpath}:{stat.st_mtime_ns}:{stat.st_size}".encode())

    return hasher.hexdigest()


class KeepDBTestRunner(DiscoverRunner):
    """DiscoverRunner that defaults to keepdb=True with auto-invalidation."""

    def __init__(self, keepdb=False, **kwargs):
        # Default to keepdb=True unless --no-keepdb was explicitly passed.
        # Note: keepdb=False here is the argparse default from Django's --keepdb flag;
        # we override it to True unless the user explicitly opts out.
        no_keepdb = kwargs.pop("no_keepdb", False)
        if not no_keepdb:
            keepdb = True
        super().__init__(keepdb=keepdb, **kwargs)

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--no-keepdb",
            action="store_true",
            dest="no_keepdb",
            help="Force fresh test database creation (overrides default --keepdb behavior).",
        )

    def setup_databases(self, **kwargs):
        if self.keepdb:
            current = _migration_fingerprint()
            try:
                with open(FINGERPRINT_FILE) as f:
                    stored = f.read().strip()
            except FileNotFoundError:
                stored = None

            if stored != current:
                # Migrations changed — force a fresh DB
                self.keepdb = False

        result = super().setup_databases(**kwargs)

        # Write fingerprint after successful DB setup
        fp = _migration_fingerprint()
        with open(FINGERPRINT_FILE, "w") as f:
            f.write(fp)

        return result
