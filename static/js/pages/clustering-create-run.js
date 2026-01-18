/**
 * Clustering Create Run Page Script
 *
 * Handles scope toggles, project/species selection, algorithm configuration,
 * and form validation for creating clustering runs.
 *
 * Expected data attributes on #clustering-create-run-data:
 * - data-project-segments-url-template: URL template for fetching project segment counts (with {project_id})
 *
 * @module pages/clustering-create-run
 */

/**
 * Initialize the clustering create run form functionality.
 */
function initClusteringCreateRun() {
  // Get configuration from data attributes
  const pageData = document.getElementById('clustering-create-run-data');
  if (!pageData) {
    console.warn('Clustering create run page data element not found');
    return;
  }

  const projectSegmentsUrlTemplate = pageData.dataset.projectSegmentsUrlTemplate;

  if (!projectSegmentsUrlTemplate) {
    console.warn('Project segments URL template not configured');
    return;
  }

  console.log('jQuery is ready, clustering create run script loaded');

  // Toggle scope sections
  $('input[name="scope"]').change(function () {
    const scope = $(this).val();
    console.log('Scope changed to:', scope);

    if (scope === 'segmentation') {
      $('#segmentation_group').slideDown(300);
      $('#project_group').slideUp(300);
      $('#segmentation').attr('required', true);
      $('#project').attr('required', false);
      $('#species').attr('required', false);
    } else {
      $('#segmentation_group').slideUp(300);
      $('#project_group').slideDown(300);
      $('#segmentation').attr('required', false);
      $('#project').attr('required', true);
      // Species required only if multiple species
    }
  });

  // Fetch project segment count when project is selected
  $('#project').change(function () {
    const projectId = $(this).val();
    console.log('Project selected:', projectId);

    // Reset displays
    $('#species_group').hide();
    $('#project_info').hide();
    $('#project_warning').hide();
    $('#species').empty().append('<option value="">Select a species...</option>');

    if (!projectId) return;

    const url = projectSegmentsUrlTemplate.replace('{project_id}', projectId);
    $.get(url, function (data) {
      console.log('Project data:', data);

      // Show species selector if multiple species
      if (data.species && data.species.length > 1) {
        $('#species_group').slideDown(300);
        $('#species').attr('required', true);
        data.species.forEach(function (s) {
          $('#species').append(
            `<option value="${s.id}">${s.name} (${s.recording_count} recordings, ${s.segment_count} segments)</option>`
          );
        });
        // Don't show info yet - wait for species selection
      } else if (data.species && data.species.length === 1) {
        // Single species - auto-select and show info
        $('#species_group').hide();
        $('#species').attr('required', false);
        $('#project_species_name').text(data.species[0].name);
        $('#project_recording_count').text(data.species[0].recording_count);
        $('#project_segment_count').text(data.species[0].segment_count);
        $('#project_info').slideDown(300);

        if (data.species[0].segment_count > 5000) {
          $('#project_warning').slideDown(300);
        }
      }
    }).fail(function (xhr) {
      console.error('Failed to fetch project data:', xhr);
      if (xhr.status === 403) {
        alert('You do not have permission to access this project.');
      }
    });
  });

  // Update counts when species is selected
  $('#species').change(function () {
    const projectId = $('#project').val();
    const speciesId = $(this).val();
    console.log('Species selected:', speciesId);

    if (!projectId || !speciesId) {
      $('#project_info').hide();
      $('#project_warning').hide();
      return;
    }

    const url =
      projectSegmentsUrlTemplate.replace('{project_id}', projectId) + '?species=' + speciesId;
    $.get(url, function (data) {
      console.log('Species data:', data);
      $('#project_species_name').text(data.species_name);
      $('#project_recording_count').text(data.recording_count);
      $('#project_segment_count').text(data.segment_count);
      $('#project_info').slideDown(300);

      if (data.warning) {
        $('#project_warning').slideDown(300);
      } else {
        $('#project_warning').hide();
      }
    });
  });

  // Show/hide number of clusters field based on algorithm type with smooth animation
  $('#algorithm').change(function () {
    const selectedOption = $(this).find(':selected');
    const isManual = selectedOption.data('manual');

    console.log('Algorithm changed:', {
      value: selectedOption.val(),
      name: selectedOption.data('name'),
      type: selectedOption.data('type'),
      isManual: isManual,
    });

    if (isManual === true || isManual === 'true') {
      console.log('Showing clusters field');
      $('#n_clusters_group').slideDown(300);
      $('#n_clusters').attr('required', true);
      $('#n_clusters_group').addClass('border-start border-primary border-3 ps-3');
    } else {
      console.log('Hiding clusters field');
      $('#n_clusters_group').slideUp(300);
      $('#n_clusters').attr('required', false);
      $('#n_clusters_group').removeClass('border-start border-primary border-3 ps-3');
    }
  });

  // Form validation feedback
  $('form').on('submit', function () {
    $(this)
      .find('button[type="submit"]')
      .html('<i class="fas fa-spinner fa-spin me-2"></i>Creating Run...');
    $(this).find('button[type="submit"]').prop('disabled', true);
  });
}

// Initialize when DOM is ready
$(document).ready(initClusteringCreateRun);
