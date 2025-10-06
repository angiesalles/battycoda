/**
 * Segment CRUD Operations - Handles create/update/delete operations
 */

export class SegmentCRUD {
    constructor(segmentationId, csrfToken) {
        this.segmentationId = segmentationId;
        this.csrfToken = csrfToken;
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

            const response = await fetch(`/segmentations/${this.segmentationId}/segments/add/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
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

            const response = await fetch(`/segmentations/${this.segmentationId}/segments/${segmentId}/edit/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
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

            const response = await fetch(`/segmentations/${this.segmentationId}/segments/${segmentId}/delete/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
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