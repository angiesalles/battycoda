/**
 * Cluster Mapping Filtering Module
 *
 * Search and filter functions for cluster mapping interface.
 */

/**
 * Filter clusters based on search text
 * @param {string} searchText - Text to search for
 */
export function filterClusters(searchText) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot filter clusters.');
    return;
  }

  searchText = searchText.toLowerCase();

  $('.cluster-box').each(function () {
    const clusterText = $(this).text().toLowerCase();
    if (clusterText.indexOf(searchText) !== -1) {
      $(this).show();
    } else {
      $(this).hide();
    }
  });
}

/**
 * Sort clusters based on the selected option
 * @param {string} sortBy - Sort field ('id', 'size', 'coherence', 'label')
 */
export function sortClusters(sortBy) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot sort clusters.');
    return;
  }

  const clusters = $('.cluster-box').toArray();

  clusters.sort(function (a, b) {
    const $a = $(a);
    const $b = $(b);

    switch (sortBy) {
      case 'id':
        return $a.data('cluster-num') - $b.data('cluster-num');
      case 'size': {
        const sizeA = parseInt($a.find('.text-muted:contains("Size")').text().split(':')[1]) || 0;
        const sizeB = parseInt($b.find('.text-muted:contains("Size")').text().split(':')[1]) || 0;
        return sizeB - sizeA;
      }
      case 'coherence': {
        const cohA =
          parseFloat($a.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
        const cohB =
          parseFloat($b.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
        return cohB - cohA;
      }
      case 'label': {
        const labelA = $a.find('h5').text().trim();
        const labelB = $b.find('h5').text().trim();
        return labelA.localeCompare(labelB);
      }
      default:
        return 0;
    }
  });

  const container = $('#clusters-list');
  clusters.forEach(function (cluster) {
    container.append(cluster);
  });
}

/**
 * Filter species sections based on the selected species
 * @param {string|number} speciesId - Species ID or 'all'
 */
export function filterSpecies(speciesId) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot filter species.');
    return;
  }

  if (speciesId === 'all') {
    $('.species-section').show();
  } else {
    $('.species-section').hide();
    $(`.species-section[data-species-id="${speciesId}"]`).show();
  }
}
