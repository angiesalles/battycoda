/**
 * Segment Search and Pagination Manager
 * Handles client-side search/filter and pagination of segments
 */

export class SegmentSearchPagination {
    constructor() {
        this.searchFilters = {
            id: '',
            minDuration: null,
            maxDuration: null,
            minTime: null,
            maxTime: null
        };
        this.currentPage = 1;
        this.pageSize = 50;
        this.filteredSegments = [];
    }

    /**
     * Apply search filters to segments
     */
    filterSegments(allSegments) {
        let filtered = [...allSegments];

        // ID filter (exact match)
        if (this.searchFilters.id) {
            const searchId = parseInt(this.searchFilters.id);
            filtered = filtered.filter(seg => seg.id === searchId);
        }

        // Duration filters (input is in milliseconds, convert to seconds)
        if (this.searchFilters.minDuration !== null) {
            filtered = filtered.filter(seg => {
                const duration = seg.offset - seg.onset;
                return duration >= (this.searchFilters.minDuration / 1000);
            });
        }

        if (this.searchFilters.maxDuration !== null) {
            filtered = filtered.filter(seg => {
                const duration = seg.offset - seg.onset;
                return duration <= (this.searchFilters.maxDuration / 1000);
            });
        }

        // Time range filters
        if (this.searchFilters.minTime !== null) {
            filtered = filtered.filter(seg => seg.onset >= this.searchFilters.minTime);
        }

        if (this.searchFilters.maxTime !== null) {
            filtered = filtered.filter(seg => seg.offset <= this.searchFilters.maxTime);
        }

        this.filteredSegments = filtered;
        return filtered;
    }

    /**
     * Get current page of segments
     */
    getCurrentPage() {
        const startIdx = (this.currentPage - 1) * this.pageSize;
        const endIdx = startIdx + this.pageSize;
        return this.filteredSegments.slice(startIdx, endIdx);
    }

    /**
     * Get total number of pages
     */
    getTotalPages() {
        return Math.ceil(this.filteredSegments.length / this.pageSize);
    }

    /**
     * Set current page
     */
    setPage(page) {
        const totalPages = this.getTotalPages();
        if (page < 1) page = 1;
        if (page > totalPages) page = totalPages;
        this.currentPage = page;
    }

    /**
     * Go to next page
     */
    nextPage() {
        this.setPage(this.currentPage + 1);
    }

    /**
     * Go to previous page
     */
    previousPage() {
        this.setPage(this.currentPage - 1);
    }

    /**
     * Go to first page
     */
    firstPage() {
        this.setPage(1);
    }

    /**
     * Go to last page
     */
    lastPage() {
        this.setPage(this.getTotalPages());
    }

    /**
     * Update search filters
     */
    updateFilters(filters) {
        this.searchFilters = { ...this.searchFilters, ...filters };
        this.currentPage = 1; // Reset to first page when filters change
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        this.searchFilters = {
            id: '',
            minDuration: null,
            maxDuration: null,
            minTime: null,
            maxTime: null
        };
        this.currentPage = 1;
    }

    /**
     * Get pagination info
     */
    getPaginationInfo() {
        const totalPages = this.getTotalPages();
        const startIdx = (this.currentPage - 1) * this.pageSize + 1;
        const endIdx = Math.min(this.currentPage * this.pageSize, this.filteredSegments.length);

        return {
            currentPage: this.currentPage,
            totalPages: totalPages,
            totalSegments: this.filteredSegments.length,
            startIdx: startIdx,
            endIdx: endIdx,
            hasNext: this.currentPage < totalPages,
            hasPrevious: this.currentPage > 1
        };
    }
}
