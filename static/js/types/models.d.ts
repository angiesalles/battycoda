/**
 * Domain model type definitions for BattyCoda
 *
 * These types mirror the Django models and are used throughout
 * the frontend JavaScript/TypeScript code.
 */

/**
 * Group (organization unit)
 */
export interface Group {
  id: number;
  name: string;
}

/**
 * Project within a group
 */
export interface Project {
  id: number;
  name: string;
  group: Group;
  description?: string;
}

/**
 * Species definition
 */
export interface Species {
  id: number;
  name: string;
  scientific_name?: string;
  image_url?: string;
}

/**
 * Call type associated with a species
 */
export interface Call {
  id: number;
  short_name: string;
  long_name?: string;
  description?: string;
  species: Species | number;
}

/**
 * Audio recording
 */
export interface Recording {
  id: number;
  name: string;
  duration: number;
  sample_rate?: number;
  channels?: number;
  file_path?: string;
  project: Project | number;
  species?: Species | number;
  created_at?: string;
  updated_at?: string;
}

/**
 * Segmentation run on a recording
 */
export interface Segmentation {
  id: number;
  recording: Recording | number;
  algorithm?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at?: string;
}

/**
 * Individual segment within a recording
 */
export interface Segment {
  id: number;
  segmentation: Segmentation | number;
  onset: number;
  offset: number;
  duration?: number;
  label?: string;
}

/**
 * Cluster from clustering analysis
 */
export interface Cluster {
  id: number;
  label?: string;
  description?: string;
  is_labeled: boolean;
  size: number;
  coherence_score?: number;
  vis_x?: number;
  vis_y?: number;
  color?: string;
}

/**
 * Clustering run
 */
export interface ClusteringRun {
  id: number;
  name?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  algorithm?: string;
  scope: 'segmentation' | 'project';
  num_clusters?: number;
  created_at?: string;
}

/**
 * Segment assigned to a cluster
 */
export interface SegmentCluster {
  id: number;
  segment: Segment | number;
  cluster: Cluster | number;
  confidence?: number;
}

/**
 * Mapping of cluster to call type
 */
export interface ClusterCallMapping {
  id: number;
  cluster: Cluster | number;
  call: Call | number;
  created_at?: string;
}

/**
 * Classification result for a segment
 */
export interface ClassificationResult {
  id: number;
  segment: Segment | number;
  predicted_call?: Call | number;
  confidence?: number;
  probabilities?: Record<string, number>;
}

/**
 * Annotation task
 */
export interface Task {
  id: number;
  segment: Segment | number;
  status: 'pending' | 'assigned' | 'completed' | 'skipped';
  assigned_to?: number;
  completed_at?: string;
  result?: string;
}

/**
 * Task batch
 */
export interface TaskBatch {
  id: number;
  name?: string;
  project: Project | number;
  total_tasks: number;
  completed_tasks: number;
  status: 'pending' | 'in_progress' | 'completed';
}
