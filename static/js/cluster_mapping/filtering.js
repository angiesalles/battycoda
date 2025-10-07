/**
 * Search and filter functions for cluster mapping
 */

/**
 * Filter clusters based on search text
 */
export function filterClusters(searchText) {
    searchText = searchText.toLowerCase();

    $('.cluster-box').each(function() {
        const clusterText = $(this).text().toLowerCase();
        if (clusterText.includes(searchText)) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

/**
 * Sort clusters based on the selected option
 */
export function sortClusters(sortBy) {
    const clusters = $('.cluster-box').toArray();

    clusters.sort((a, b) => {
        const $a = $(a);
        const $b = $(b);

        switch (sortBy) {
            case 'id':
                return $a.data('cluster-num') - $b.data('cluster-num');
            case 'size':
                const sizeA = parseInt($a.find('.text-muted:contains("Size")').text().split(':')[1]);
                const sizeB = parseInt($b.find('.text-muted:contains("Size")').text().split(':')[1]);
                return sizeB - sizeA;
            case 'coherence':
                const cohA = parseFloat($a.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                const cohB = parseFloat($b.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                return cohB - cohA;
            case 'label':
                const labelA = $a.find('h5').text().trim();
                const labelB = $b.find('h5').text().trim();
                return labelA.localeCompare(labelB);
            default:
                return 0;
        }
    });

    const container = $('#clusters-list');
    clusters.forEach(cluster => {
        container.append(cluster);
    });
}

/**
 * Filter species sections based on the selected species
 */
export function filterSpecies(speciesId) {
    if (speciesId === 'all') {
        $('.species-section').show();
    } else {
        $('.species-section').hide();
        $(`.species-section[data-species-id="${speciesId}"]`).show();
    }
}
