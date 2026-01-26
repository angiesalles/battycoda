# BattyCoda

BattyCoda is a web-based platform for annotating and classifying bat vocalizations. It provides tools for segmenting audio recordings, running machine learning classifiers, and managing collaborative annotation workflows.

## Table of Contents

1. [Pre-Annotation Processing](#1-pre-annotation-processing)
2. [Setting up Species and Projects](#2-setting-up-species-and-projects)
3. [Uploading Recordings](#3-uploading-recordings)
4. [From Upload to Task Batch](#4-from-upload-to-task-batch)
5. [Annotating Calls](#5-annotating-calls)
6. [Exporting Data](#6-exporting-data)
7. [FAQ](#faq)

## 1. Pre-Annotation Processing

Before uploading recordings, it is recommended to filter out as much noise as possible. Tools such as SonoBat's Noise Scrubbing can help identify and remove noise files. Applying a high-pass filter can also reduce noise interference with the automatic segmenter. Filter settings will vary by species—note that many social calls are lower in frequency than echolocation calls, so review your data before setting filter thresholds.

If your lab has existing segmentation workflows or previously segmented recordings, those segments can be imported into BattyCoda. Tools like SASLab can be used for automatic segmentation.

BattyCoda works best with short audio files. Files longer than one minute should be split before upload.

## 2. Setting up Species and Projects

Organization admins can add new species to the system. Each species requires:
- A repertoire image (JPEG format)
- A list of call types (entered manually or imported from a text file)

**Tip:** Include "Noise" and "Unknown" as call types to simplify annotation.

![Species setup interface][image1]

## 3. Uploading Recordings

Recordings can be uploaded with or without pre-existing segmentation. Before uploading, determine the appropriate group and project:

- **Groups** control access permissions. For example, you might separate files for student annotators from test files.
- **Projects** organize recordings by experiment, field season, or other logical groupings. Task filtering is based on project membership.

### Uploading Segmented Recordings

To import existing segments, prepare a CSV or Excel file with segment start and end times, then convert it to a pickle file using the `ImprovedBatPickle.py` script (available in the repository). Use `picklecheck.py` to verify the pickle file format before upload.

Upload options:
- **Single file:** Use the "New Recording" button, then upload the pickle file from the recording page
- **Small batches (~50 files):** Use the batch processing feature with ZIP archives
- **Large batches:** Use the API for bulk uploads (see example code in the repository)

### Uploading Unsegmented Recordings

- **Single file:** Use the "New Recording" button
- **Small batches (~50 files):** Use the batch processing feature
- **Large batches:** Use the API implementation

## 4. From Upload to Task Batch

The navigation tabs reflect the processing workflow:

![Navigation tabs][image2]

### Segmentation

For unsegmented files, open a recording and click "Auto Segment":

![Auto segment interface][image3]

Set the minimum duration to match the shortest expected call for your species (typically the echolocation call duration).

### Classification

Run classification on segmented recordings:
- **Single recording:** Click "New Classification Run"
- **Batch processing:** Use "Classify Unclassified Segments"

![Classifier selection][image4]

Select the appropriate classifier for your species. For species without a trained classifier, use "Dummy Classification."

### Creating Task Batches

After classification, create task batches from the Classification tab:

![Task batch creation][image5]

You can set a confidence threshold to exclude high-confidence predictions from manual review (recommended only for species with validated classifiers).

All of these operations can also be performed via the API, which is recommended for large datasets.

## 5. Annotating Calls

The annotation interface displays:

![Annotation interface][image6]

**Center panel:** The spectrogram view with two modes:
- **Detailed view:** Zoomed in on the segment being labeled (centered after the 0-second mark)
- **Overview:** Zoomed out to show surrounding context

**Below the spectrogram:**
- Channel selector (for multi-microphone recordings)
- Audio playback controls (pitch-shifted for audibility)

**Left panel:**
- Species repertoire reference image
- Recording metadata (species, recording name, segment number, duration)
- Task batch and project information
- Navigation buttons (previous/skip)

**Right panel:**
- Call type buttons for labeling
- Classifier's predicted label appears at the top
- "Mark as Done" and "Next Task" buttons

## 6. Exporting Data

### Exporting Annotations

From the Task Batch page, filter by project and click "Download Completed Batches" to receive a ZIP file containing Excel exports for each recording:

![Export example][image7]

The export includes:
- **Label:** Human annotation
- **Classification:** Classifier prediction (blank for dummy classification)

### Exporting Parameters

Classification parameters can be exported from the Classification tab:

![Parameter export button][image8]

The parameter export format:

![Parameter export example][image9]

Combine annotation labels with acoustic parameters for analysis. Example code is available in the repository.

## FAQ

**Q: I encountered an error. What should I do?**

A: Please submit an issue report on [GitHub](https://github.com/angiesalles/battycoda/issues). We actively monitor and address reported issues.

**Q: My species doesn't have a documented repertoire. How do I proceed?**

A: You can build the repertoire as you annotate. Add a "New Call" call type to capture undescribed vocalizations, then update the repertoire as patterns emerge. The Clustering feature (currently in development) will help identify call type groupings automatically.

[image1]: docs/images/image1.png
[image2]: docs/images/image2.png
[image3]: docs/images/image3.png
[image4]: docs/images/image4.png
[image5]: docs/images/image5.png
[image6]: docs/images/image6.png
[image7]: docs/images/image7.png
[image8]: docs/images/image8.png
[image9]: docs/images/image9.png
