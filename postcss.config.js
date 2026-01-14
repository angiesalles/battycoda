/**
 * PostCSS Configuration
 *
 * Plugins:
 * - autoprefixer: Adds vendor prefixes for browser compatibility
 * - cssnano: Minifies CSS in production builds
 */
export default {
  plugins: {
    autoprefixer: {},
    // Only minify in production
    ...(process.env.NODE_ENV === 'production' ? { cssnano: {} } : {}),
  },
};
