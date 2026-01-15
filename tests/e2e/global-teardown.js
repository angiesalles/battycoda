/**
 * Playwright global teardown script.
 *
 * This script runs once after all tests to clean up the test environment.
 * It removes test users, groups, species, and projects from the database.
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Global teardown function called by Playwright after all tests.
 */
async function globalTeardown() {
  console.log('\n🧹 Cleaning up E2E test data...\n');

  try {
    // Activate virtual environment and run Django management command
    // The --force flag ensures recordings are also cleaned up
    const { stdout, stderr } = await execAsync(
      'source venv/bin/activate && python manage.py cleanup_e2e_tests --force',
      {
        cwd: process.cwd(),
        shell: '/bin/bash',
        timeout: 30000, // 30 second timeout
      }
    );

    if (stdout) {
      console.log(stdout);
    }

    if (stderr) {
      // Django sometimes outputs info to stderr, only show if it looks like an error
      if (stderr.toLowerCase().includes('error') || stderr.toLowerCase().includes('traceback')) {
        console.error('Teardown stderr:', stderr);
      }
    }

    console.log('✅ E2E test data cleanup complete!\n');
  } catch (error) {
    // Log but don't fail on teardown errors - tests have already completed
    console.error('⚠️ Warning: Failed to clean up E2E test data:');
    console.error(error.message);
    if (error.stdout) console.log('stdout:', error.stdout);
    if (error.stderr) console.error('stderr:', error.stderr);

    // Don't throw - we don't want to fail the test run just because cleanup failed
    console.log('Note: You may need to manually run "python manage.py cleanup_e2e_tests --force"');
  }
}

export default globalTeardown;
