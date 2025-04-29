# BattyCoda User Guide

This guide explains how to use BattyCoda's features for bat vocalization analysis and research.

## Contents

1. [Getting Started](#getting-started)
2. [User Interface Overview](#user-interface-overview)
3. [Working with Recordings](#working-with-recordings)
4. [Segmentation](#segmentation)
5. [Task Management](#task-management)
6. [Classification](#classification)
7. [Projects and Organization](#projects-and-organization)
8. [Group Collaboration](#group-collaboration)
9. [Advanced Features](#advanced-features)

## Getting Started

### Creating an Account

1. Navigate to the BattyCoda login page
2. Click "Register" to create a new account
3. Fill in your details and submit the registration form
4. Use the email verification link sent to your inbox to verify your account

### Setting Up Your First Group

1. After logging in, click on your username in the top-right corner
2. Select "Create New Group" from the dropdown menu
3. Fill in the group name and description
4. Add initial members (optional)
5. Set group preferences

## User Interface Overview

### Navigation Menu

The main navigation menu provides access to all major features:

- **Home**: Dashboard with overview of your recent activity
- **Recordings**: List and manage audio recordings
- **Segmentation**: Tools for automated and manual segmentation
- **Classification**: Machine learning models and classification tools
- **Task Batches**: Manage annotation and verification tasks
- **Projects**: Organize your research into projects
- **Species**: Manage bat species and call types
- **Users**: Manage group members (admin only)

### Dashboard

The dashboard provides an overview of:

- Recent activity
- Task status
- Available recordings
- Pending annotations
- Active projects

## Working with Recordings

### Uploading Recordings

1. Navigate to the Recordings section
2. Click "Upload Recording"
3. Fill in the metadata form (name, date, location, etc.)
4. Select the project and species
5. Choose the WAV file to upload
6. Submit the form

### Managing Recordings

- **View Details**: Click on a recording name to access its details
- **Edit Metadata**: Use the edit button on the recording detail page
- **Delete**: Use the delete option (caution: this will remove all associated segments and tasks)
- **Batch Upload**: Use the batch upload feature for multiple files

## Segmentation

### Automatic Segmentation

1. Navigate to the Segmentation section
2. Select "Batch Segmentation" for multiple recordings or select a specific recording
3. Choose the segmentation algorithm
4. Set parameters (min duration, threshold, smoothing)
5. Start the segmentation process

### Manual Segmentation

1. Open a recording's detail page
2. Click "Segment Recording"
3. Use the waveform viewer to identify calls
4. Click and drag to create segments
5. Adjust segment boundaries by dragging edges
6. Save your segments

### Editing Segmentation Results

1. Open a recording with existing segmentation
2. View the segments listed below the waveform
3. Click on a segment to select it
4. Use the controls to adjust, delete, or add notes
5. Create tasks from selected segments

## Task Management

### Creating Task Batches

1. Navigate to Task Batches
2. Click "Create Task Batch"
3. Select the source (manually or from segments)
4. Choose the recordings and segments to include
5. Assign to the appropriate project and species
6. Submit the form

### Annotating Tasks

1. Open a task batch
2. Click on a task to open the annotation view
3. View the spectrogram of the bat call
4. Use the tools to:
   - Adjust spectrogram parameters
   - Select a call type
   - Add notes
   - Mark as "Done" when complete
5. Navigate between tasks using the arrows

## Classification

### Training a Classifier

1. Navigate to Classification
2. Select "Create Classifier"
3. Choose the species
4. Select the training data (annotated task batches)
5. Choose algorithm type (KNN or LDA)
6. Set training parameters
7. Start training

### Running Classification

1. Navigate to Classification
2. Select "Create Run"
3. Choose the classifier to use
4. Select recordings to process
5. Start the classification run
6. Review results and apply to tasks

## Projects and Organization

### Creating Projects

1. Navigate to Projects
2. Click "Create Project"
3. Enter name and description
4. Set permissions if needed
5. Save the project

### Managing Species

1. Navigate to Species
2. Add new species with "Create Species"
3. Upload an image (optional)
4. Add call types for the species
5. Save the species

## Group Collaboration

### Inviting Users

1. Navigate to Users (admin only)
2. Click "Invite User"
3. Enter email address
4. Set permission level
5. Send invitation

### Managing Permissions

1. Navigate to Users
2. Select a user
3. Modify their role (admin, editor, viewer)
4. Save changes

## Advanced Features

### Exporting Data

1. From any list view, use the export options
2. Choose export format (CSV, JSON)
3. Select data fields to include
4. Download the file

### R Model Integration

1. Train models using the Classification interface
2. Models are stored in the data/models directory
3. Advanced users can access the R server directly for custom analysis

### Custom Segmentation Algorithms

1. Navigate to Segmentation Settings (admin only)
2. Configure algorithm parameters
3. Test on sample recordings
4. Save as a new algorithm profile for future use

For more detailed information or technical questions, please refer to the [Developer Guide](DEVELOPER_GUIDE.md) or contact your system administrator.