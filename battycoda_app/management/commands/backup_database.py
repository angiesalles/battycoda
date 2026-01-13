import os
import subprocess
import tempfile
from datetime import datetime

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Backup the database to S3'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bucket',
            type=str,
            default='backup-battycoda',
            help='S3 bucket name for backup storage'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default='database-backups/',
            help='S3 prefix for backup files'
        )

    def handle(self, *args, **options):
        bucket_name = options['bucket']
        prefix = options['prefix']
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        
        # Create timestamp for backup filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"battycoda_backup_{timestamp}.sql"
        
        # Create temporary file for the backup
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.sql') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Create pg_dump command (use full path for celery worker compatibility)
            pg_dump_cmd = [
                '/usr/bin/pg_dump',
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                '--format=plain',
                '--file=' + tmp_path
            ]
            
            # Add connection parameters
            if 'HOST' in db_config:
                pg_dump_cmd.extend(['--host', db_config['HOST']])
            if 'PORT' in db_config:
                pg_dump_cmd.extend(['--port', str(db_config['PORT'])])
            if 'USER' in db_config:
                pg_dump_cmd.extend(['--username', db_config['USER']])
            
            # Add database name
            pg_dump_cmd.append(db_config['NAME'])
            
            # Set password via environment variable if available
            env = os.environ.copy()
            if 'PASSWORD' in db_config:
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            self.stdout.write(f"Creating database backup...")
            
            # Execute pg_dump
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise CommandError(f"pg_dump failed: {result.stderr}")
            
            # Upload to S3
            self.stdout.write(f"Uploading backup to S3...")
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY,
                region_name=settings.AWS_SES_REGION_NAME
            )
            
            s3_key = f"{prefix}{backup_filename}"
            
            # Upload file to S3
            s3_client.upload_file(tmp_path, bucket_name, s3_key)
            
            # Get file size for reporting
            file_size = os.path.getsize(tmp_path)
            file_size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Database backup completed successfully!\n"
                    f"File: {backup_filename}\n"
                    f"Size: {file_size_mb:.2f} MB\n"
                    f"S3 Location: s3://{bucket_name}/{s3_key}"
                )
            )
            
        except Exception as e:
            raise CommandError(f"Backup failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)