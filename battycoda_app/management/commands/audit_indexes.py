"""Management command to audit database indexes for ForeignKey fields."""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check that all ForeignKey fields have corresponding database indexes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Create missing indexes (use CREATE INDEX CONCURRENTLY)",
        )

    def handle(self, *args, **options):
        fix = options["fix"]

        # Get all indexes in the database
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            existing_indexes = {}
            for table, indexdef in cursor.fetchall():
                existing_indexes.setdefault(table, []).append(indexdef)

        missing = []

        for model in apps.get_app_config("battycoda_app").get_models():
            table = model._meta.db_table

            for field in model._meta.get_fields():
                if not hasattr(field, "column") or not field.column:
                    continue
                if not getattr(field, "db_index", False) and not (
                    hasattr(field, "remote_field") and field.remote_field and getattr(field, "db_index", True)
                ):
                    continue

                # For ForeignKey fields, check if there's an index on the column
                is_fk = hasattr(field, "remote_field") and field.remote_field
                if not is_fk:
                    continue

                column = field.column
                table_indexes = existing_indexes.get(table, [])

                has_index = any(f"({column})" in idx or f"( {column} )" in idx for idx in table_indexes)

                if not has_index:
                    missing.append((table, column, field.name, model.__name__))

        if not missing:
            self.stdout.write(self.style.SUCCESS("All ForeignKey fields have database indexes."))
            return

        self.stdout.write(self.style.WARNING(f"Found {len(missing)} ForeignKey fields without indexes:"))
        for table, column, field_name, model_name in missing:
            self.stdout.write(f"  {model_name}.{field_name} ({table}.{column})")

            if fix:
                index_name = f"{table}_{column}_idx"
                # Truncate to Postgres max identifier length
                if len(index_name) > 63:
                    index_name = index_name[:63]

                with connection.cursor() as cursor:
                    sql = f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{index_name}" ON "{table}" ("{column}")'
                    self.stdout.write(f"    Creating: {sql}")
                    cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS(f"    Created index {index_name}"))

        if not fix:
            self.stdout.write("\nRun with --fix to create missing indexes.")
