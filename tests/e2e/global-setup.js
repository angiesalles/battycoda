/**
 * Playwright global setup script.
 *
 * This script runs once before all tests to set up the test environment.
 * It configures the test database and creates test fixtures.
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Environment for all Django commands - use test database
const testEnv = {
  ...process.env,
  DJANGO_TEST_MODE: 'true',
};

/**
 * Run a Django management command with test database.
 */
async function runDjangoCommand(command, description) {
  console.log(`  → ${description}...`);
  const { stdout, stderr } = await execAsync(
    `source venv/bin/activate && ${command}`,
    {
      cwd: process.cwd(),
      shell: '/bin/bash',
      timeout: 60000, // 60 second timeout
      env: testEnv,
    }
  );

  if (stdout) {
    // Only show output if verbose or if it contains important info
    const lines = stdout.trim().split('\n').filter(line =>
      line.includes('Created') ||
      line.includes('✓') ||
      line.includes('Applying') ||
      line.includes('OK')
    );
    if (lines.length > 0) {
      console.log(`    ${lines.slice(0, 5).join('\n    ')}`);
      if (lines.length > 5) {
        console.log(`    ... and ${lines.length - 5} more`);
      }
    }
  }

  if (stderr) {
    // Django sometimes outputs info to stderr, only show if it looks like an error
    if (stderr.toLowerCase().includes('error') || stderr.toLowerCase().includes('traceback')) {
      console.error('    Error:', stderr);
      throw new Error(stderr);
    }
  }
}

/**
 * Global setup function called by Playwright before all tests.
 */
async function globalSetup() {
  console.log('\n🔧 Setting up E2E test environment...\n');
  console.log('📦 Using test database: battycoda_test\n');

  try {
    // Step 1: Run migrations to ensure test database schema is up to date
    await runDjangoCommand(
      'python manage.py migrate --run-syncdb',
      'Running database migrations'
    );

    // Step 2: Initialize default data (species, algorithms, etc.)
    await runDjangoCommand(
      'python manage.py initialize_defaults',
      'Initializing default data'
    );

    // Step 3: Set up E2E test fixtures (users, groups, projects)
    // The --reset flag ensures we start with clean test data
    await runDjangoCommand(
      'python manage.py setup_e2e_tests --reset',
      'Creating E2E test fixtures'
    );

    console.log('\n✅ E2E test environment ready!\n');
  } catch (error) {
    console.error('\n❌ Failed to set up E2E test environment:');
    console.error(error.message);
    if (error.stdout) console.log('stdout:', error.stdout);
    if (error.stderr) console.error('stderr:', error.stderr);

    // Throw to fail the test run if setup fails
    throw new Error(`E2E setup failed: ${error.message}`);
  }
}

export default globalSetup;
