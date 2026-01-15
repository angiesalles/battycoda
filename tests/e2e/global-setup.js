/**
 * Playwright global setup script.
 *
 * This script runs once before all tests to set up the test environment.
 * It creates test users, groups, species, and projects in the database.
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * Global setup function called by Playwright before all tests.
 */
async function globalSetup() {
  console.log('\n🔧 Setting up E2E test data...\n');

  try {
    // Activate virtual environment and run Django management command
    // The --reset flag ensures we start with clean test data
    const { stdout, stderr } = await execAsync(
      'source venv/bin/activate && python manage.py setup_e2e_tests --reset',
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
        console.error('Setup stderr:', stderr);
      }
    }

    console.log('✅ E2E test data setup complete!\n');
  } catch (error) {
    console.error('❌ Failed to set up E2E test data:');
    console.error(error.message);
    if (error.stdout) console.log('stdout:', error.stdout);
    if (error.stderr) console.error('stderr:', error.stderr);

    // Throw to fail the test run if setup fails
    throw new Error(`E2E setup failed: ${error.message}`);
  }
}

export default globalSetup;
