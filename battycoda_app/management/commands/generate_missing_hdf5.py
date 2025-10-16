"""
Management command to generate missing HDF5 spectrogram files for recordings.

This command processes recordings that don't have HDF5 files, generating them
in the background with CPU throttling to avoid overloading the server.
"""
import os
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from battycoda_app.models.recording import Recording
from battycoda_app.audio.task_modules.spectrogram.hdf5_generation import generate_hdf5_spectrogram


class Command(BaseCommand):
    help = 'Generate missing HDF5 spectrogram files for all recordings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=None,
            help='Maximum number of recordings to process (default: all)'
        )
        parser.add_argument(
            '--sleep-multiplier',
            type=float,
            default=1.0,
            help='Multiplier for adaptive sleep time (sleeps for processing_time * multiplier, default: 1.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_multiplier = options['sleep_multiplier']
        dry_run = options['dry_run']

        # Find recordings without HDF5 files
        recordings = Recording.objects.filter(hidden=False).order_by('id')

        missing_hdf5 = []
        for recording in recordings:
            if not recording.spectrogram_file:
                missing_hdf5.append(recording)
                continue

            # Check if file exists on disk
            if recording.spectrogram_file:
                base_name = recording.spectrogram_file.replace('.png', '').replace('.h5', '')
                spectrogram_filename = f"{base_name}.h5"
                output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
                output_path = os.path.join(output_dir, spectrogram_filename)

                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    missing_hdf5.append(recording)

        total_missing = len(missing_hdf5)
        self.stdout.write(self.style.SUCCESS(f'Found {total_missing} recordings without HDF5 files'))

        if batch_size:
            missing_hdf5 = missing_hdf5[:batch_size]
            self.stdout.write(f'Processing first {len(missing_hdf5)} recordings')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No files will be generated'))
            for i, recording in enumerate(missing_hdf5, 1):
                self.stdout.write(f'  {i}. Recording {recording.id}: {recording.name}')
            return

        processed = 0
        errors = 0

        for i, recording in enumerate(missing_hdf5, 1):
            try:
                self.stdout.write(f'[{i}/{len(missing_hdf5)}] Processing recording {recording.id}: {recording.name}')

                # Check WAV file exists
                if not recording.wav_file or not os.path.exists(recording.wav_file.path):
                    self.stdout.write(self.style.ERROR(f'  Skipping - WAV file not found'))
                    errors += 1
                    continue

                file_size_mb = recording.wav_file.size / (1024 * 1024)
                self.stdout.write(f'  WAV file size: {file_size_mb:.1f} MB')

                # Generate HDF5
                start_time = time.time()
                result = generate_hdf5_spectrogram(recording.id)
                elapsed = time.time() - start_time

                if result.get('status') == 'success':
                    if result.get('cached'):
                        self.stdout.write(self.style.SUCCESS(f'  HDF5 already exists (took {elapsed:.1f}s)'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  HDF5 generated successfully (took {elapsed:.1f}s)'))
                    processed += 1
                else:
                    error_msg = result.get('message') or result.get('error', 'Unknown error')
                    self.stdout.write(self.style.ERROR(f'  Failed: {error_msg}'))
                    errors += 1
                    elapsed = 0

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))
                errors += 1
                elapsed = 0

            # Sleep between recordings to limit CPU usage (adaptive based on processing time)
            if i < len(missing_hdf5):
                sleep_time = max(1, int(elapsed * sleep_multiplier))
                self.stdout.write(f'  Sleeping for {sleep_time} seconds...')
                time.sleep(sleep_time)

        self.stdout.write(self.style.SUCCESS(f'\nCompleted: {processed} processed, {errors} errors'))
