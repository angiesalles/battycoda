/**
 * Search and filter functions for cluster mapping
 */
(function(ClusterMapping) {
    'use strict';

    /**
     * Filter clusters based on search text
     */
    ClusterMapping.filterClusters = function(searchText) {
        searchText = searchText.toLowerCase();

        $('.cluster-box').each(function() {
            var clusterText = $(this).text().toLowerCase();
            if (clusterText.indexOf(searchText) !== -1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    };

    /**
     * Sort clusters based on the selected option
     */
    ClusterMapping.sortClusters = function(sortBy) {
        var clusters = $('.cluster-box').toArray();

        clusters.sort(function(a, b) {
            var $a = $(a);
            var $b = $(b);

            switch (sortBy) {
                case 'id':
                    return $a.data('cluster-num') - $b.data('cluster-num');
                case 'size':
                    var sizeA = parseInt($a.find('.text-muted:contains("Size")').text().split(':')[1]) || 0;
                    var sizeB = parseInt($b.find('.text-muted:contains("Size")').text().split(':')[1]) || 0;
                    return sizeB - sizeA;
                case 'coherence':
                    var cohA = parseFloat($a.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                    var cohB = parseFloat($b.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                    return cohB - cohA;
                case 'label':
                    var labelA = $a.find('h5').text().trim();
                    var labelB = $b.find('h5').text().trim();
                    return labelA.localeCompare(labelB);
                default:
                    return 0;
            }
        });

        var container = $('#clusters-list');
        clusters.forEach(function(cluster) {
            container.append(cluster);
        });
    };

    /**
     * Filter species sections based on the selected species
     */
    ClusterMapping.filterSpecies = function(speciesId) {
        if (speciesId === 'all') {
            $('.species-section').show();
        } else {
            $('.species-section').hide();
            $('.species-section[data-species-id="' + speciesId + '"]').show();
        }
    };

})(window.ClusterMapping = window.ClusterMapping || {});
