# BattyCoda

<p align="center">
  <img src="static/img/brandmark-design.png" alt="BattyCoda Logo" width="200"/>
</p>

BattyCoda is an advanced platform for bat vocalization analysis and research. It helps researchers process, visualize, and analyze bat vocalizations through a comprehensive set of tools for audio management, segmentation, and species classification.

## What is BattyCoda?

BattyCoda is a web-based application designed specifically for bat researchers and ecologists to analyze bat vocalizations. It combines signal processing, machine learning, and a user-friendly interface to streamline the analysis workflow from raw audio to classified bat calls.

The platform enables researchers to:
- Upload and process bat call recordings
- Automatically detect and segment bat calls
- Visualize spectrograms with adjustable parameters
- Classify calls using machine learning models
- Manage research projects collaboratively
- Organize and tag data effectively

## Key Features

### Audio Recording Management
- Upload and organize bat vocalization recordings (.wav files)
- Automatic spectrogram generation
- Track metadata like recording date, location, and equipment used

### Segmentation System
- Automatically detect bat calls in longer recordings
- Multiple segmentation algorithms for different recording conditions
- Manually edit segmentation results for greater accuracy

### Task-Based Annotation
- Organize research tasks into batches
- Assign tasks to team members
- Track annotation progress

### Species Classification
- Train machine learning models on annotated data
- KNN and LDA classifier options
- Automated classification of new recordings

### Collaborative Workspace
- Group-based organization structure
- Share projects and recordings with colleagues
- User permission management

### Project Organization
- Organize recordings, tasks, and analyses into projects
- Track progress across multiple research initiatives
- Filter and search capabilities

## Key Concepts

### Recordings
Full audio recordings that may contain multiple bat calls, typically in WAV format. Recordings are stored and organized by project and species.

### Segments
Individual sections within a recording that contain a single bat call or event of interest, identified by start and end timestamps.

### Tasks
Actions to be performed on segments, such as annotation, verification, or analysis. Tasks can be organized into batches for efficient workflow management.

### Spectrograms
Visual representations of bat calls showing frequency (Y-axis) over time (X-axis), useful for visualizing the acoustic characteristics of calls.

### Species & Call Types
BattyCoda organizes data by bat species and their associated call types, such as echolocation calls, social calls, or distress calls.

### Classifiers
Machine learning models trained on annotated data to automatically identify bat species or call types from new recordings.

## Architecture

BattyCoda consists of several integrated components:

- **Django Web Application**: Core application with user interface and data management
- **R Statistical Engine**: Handles advanced audio processing and machine learning 
- **Celery Task Queue**: Manages asynchronous processing for segmentation and classification
- **PostgreSQL Database**: Stores all metadata and organizational structure
- **Docker**: Containerizes all components for easy deployment and scaling

## Documentation

For more detailed information, please see the following documentation:

- [Installation Guide](docs/INSTALLATION.md) - Setup instructions for server and local installations
- [User Guide](docs/USER_GUIDE.md) - How to use BattyCoda's features
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Information for developers contributing to BattyCoda
- [API Documentation](docs/API.md) - Details about the API endpoints (for integration)

## Research Applications

BattyCoda was designed to support various research applications, including:

- Acoustic bat monitoring for conservation
- Temporal and spatial distribution studies
- Species identification and population surveys
- Behavioral research on bat communication
- Long-term ecological monitoring

## License

[License information to be added]

## Acknowledgements

[To be added - credits to contributors, research institutions, etc.]