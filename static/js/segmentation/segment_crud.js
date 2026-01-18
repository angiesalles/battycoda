/**
 * Segment CRUD Operations - Handles create/update/delete operations
 */

export class SegmentCRUD {
  /**
   * @param {number} segmentationId - The segmentation ID
   * @param {string} csrfToken - CSRF token for requests
   * @param {Object} urls - URL templates for API endpoints
   * @param {string} urls.add - URL template for adding segments (e.g., "/segmentations/{segmentationId}/segments/add/")
   * @param {string} urls.edit - URL template for editing segments (e.g., "/segmentations/{segmentationId}/segments/{segmentId}/edit/")
   * @param {string} urls.delete - URL template for deleting segments (e.g., "/segmentations/{segmentationId}/segments/{segmentId}/delete/")
   */
  constructor(segmentationId, csrfToken, urls = {}) {
    this.segmentationId = segmentationId;
    this.csrfToken = csrfToken;

    // URL templates - use provided URLs or fall back to defaults for backwards compatibility
    this.urls = {
      add: urls.add || `/segmentations/${segmentationId}/segments/add/`,
      edit: urls.edit || `/segmentations/${segmentationId}/segments/{segmentId}/edit/`,
      delete: urls.delete || `/segmentations/${segmentationId}/segments/{segmentId}/delete/`,
    };
  }

  /**
   * Interpolate URL template with provided values
   * @param {string} template - URL template with {placeholders}
   * @param {Object} values - Key-value pairs to substitute
   * @returns {string} - Interpolated URL
   */
  interpolateUrl(template, values = {}) {
    let url = template;
    for (const [key, value] of Object.entries(values)) {
      url = url.replace(`{${key}}`, value);
    }
    return url;
  }

  // Create a new segment
  async createSegment(segmentData) {
    try {
      const formData = new FormData();
      formData.append('csrfmiddlewaretoken', this.csrfToken);
      formData.append('onset', segmentData.onset);
      formData.append('offset', segmentData.offset);
      if (segmentData.name) {
        formData.append('name', segmentData.name);
      }
      if (segmentData.notes) {
        formData.append('notes', segmentData.notes);
      }

      const response = await fetch(this.urls.add, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        return data.segment;
      } else {
        throw new Error(data.error || 'Failed to create segment');
      }
    } catch (error) {
      console.error('Error creating segment:', error);
      throw error;
    }
  }

  // Update an existing segment
  async updateSegment(segmentId, segmentData) {
    try {
      const formData = new FormData();
      formData.append('csrfmiddlewaretoken', this.csrfToken);
      formData.append('onset', segmentData.onset);
      formData.append('offset', segmentData.offset);
      if (segmentData.name) {
        formData.append('name', segmentData.name);
      }
      if (segmentData.notes) {
        formData.append('notes', segmentData.notes);
      }

      const url = this.interpolateUrl(this.urls.edit, { segmentId });
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        return data.segment;
      } else {
        throw new Error(data.error || 'Failed to update segment');
      }
    } catch (error) {
      console.error('Error updating segment:', error);
      throw error;
    }
  }

  // Delete a segment
  async deleteSegment(segmentId) {
    try {
      const formData = new FormData();
      formData.append('csrfmiddlewaretoken', this.csrfToken);

      const url = this.interpolateUrl(this.urls.delete, { segmentId });
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
        },
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        return true;
      } else {
        throw new Error(data.error || 'Failed to delete segment');
      }
    } catch (error) {
      console.error('Error deleting segment:', error);
      throw error;
    }
  }
}
