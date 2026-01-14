// Store clustering run ID for API calls (will be set by template)
let clusteringRunId;

// Store existing mappings (will be set by template)
const existingMappings = [];

// Initialize the application after jQuery is definitely loaded
document.addEventListener('DOMContentLoaded', function () {
  // Make sure jQuery is loaded
  if (typeof jQuery === 'undefined') {
    console.error('jQuery is not loaded. Waiting...');
    // Try again in a short while
    setTimeout(function () {
      if (typeof jQuery !== 'undefined') {
        console.log('jQuery is now loaded, initializing...');
        // Set up CSRF token for AJAX requests
        setupCSRF();
        // Load our script
        const script = document.createElement('script');
        script.src = clusterMappingJsUrl;
        document.body.appendChild(script);
      } else {
        console.error(
          'jQuery could not be loaded after waiting. Cluster mapping functionality may not work.'
        );
      }
    }, 1000);
  } else {
    console.log('jQuery is already loaded, initializing...');
    // Set up CSRF token for AJAX requests
    setupCSRF();
    // Load our script
    const script = document.createElement('script');
    script.src = clusterMappingJsUrl;
    document.body.appendChild(script);
  }
});

function setupCSRF() {
  // Get CSRF token
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  console.log('CSRF token found:', csrftoken ? 'Yes' : 'No');

  // Set up jQuery AJAX to always send CSRF token
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      if (!this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      }
    },
  });
}
