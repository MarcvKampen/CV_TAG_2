# Recruitee Tagger V3.0

A comprehensive CV processing system that automates candidate analysis using AI and OCR technology. This application retrieves CVs from Recruitee, processes them with advanced text extraction and AI analysis, and uploads structured tags back to the recruitment platform.

## Quick Start

### For End Users (Non-Technical)
1. **Download** the latest executable from releases
2. **Run** `Recruitee_Tagger_V3.exe`
3. **Configure** your API keys in the Configuration tab
4. **Start processing** in the Processing tab

### For Developers
```bash
# Clone and setup
git clone <repository-url>
cd NEW
pip install -r requirements.txt
python cv_processing_gui.py
```

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Technical Documentation](#technical-documentation)
- [API Integration](#api-integration)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [Contributing](#contributing)

## Overview

### What It Does
The Recruitee Tagger V3.0 automates the tedious process of analyzing CVs by:

1. **Retrieving** untagged candidates from Recruitee
2. **Downloading** PDF CVs automatically
3. **Extracting** text using advanced OCR technology
4. **Analyzing** content with AI to identify key information
5. **Generating** structured Excel reports
6. **Uploading** tags back to Recruitee

### Business Value
- **Time Savings**: Process 100+ CVs in minutes instead of hours
- **Consistency**: Standardized analysis across all candidates
- **Accuracy**: AI-powered extraction reduces human error
- **Scalability**: Handle large recruitment campaigns efficiently

## Features

### Core Functionality
- **Smart CV Retrieval**: Automatically finds untagged candidates
- **PDF Processing**: Handles various PDF formats and layouts
- **AI Analysis**: Extracts education, experience, skills, and more
- **Excel Reporting**: Generates detailed analysis reports
- **Recruitee Integration**: Seamless upload of structured tags

### User Interface
- **Modern GUI**: Clean, intuitive PyQt6 interface
- **Real-time Progress**: Live updates during processing
- **Configuration Management**: Save and load settings
- **Secure Storage**: Encrypted API key handling
- **Preview Mode**: Review results before upload

### Technical Features
- **Multi-threading**: Non-blocking GUI during processing
- **Error Handling**: Robust error recovery and logging
- **Retry Logic**: Automatic retry for failed operations
- **File Management**: Organized output and temporary files
- **PyInstaller Ready**: Easy deployment as standalone executable

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **Network**: Internet connection for API access

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB
- **Storage**: 5 GB free space
- **Network**: Stable broadband connection

### Development Requirements
- **Python**: 3.8+
- **PyQt6**: Latest version
- **Dependencies**: See requirements.txt

## Installation

### Option 1: Standalone Executable (Recommended for Users)
1. Download `Recruitee_Tagger_V3.exe` from releases
2. Extract to desired folder
3. Run the executable
4. No additional installation required

### Option 2: Python Development Setup
```bash
# Clone repository
git clone <repository-url>
cd NEW

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
python cv_processing_gui.py
```

### Option 3: Build from Source
```bash
# Install build tools
pip install pyinstaller

# Build executable
python build_exe.py
# OR
pyinstaller cv_processing_gui.spec
```

## Configuration

### API Keys Setup

#### Recruitee API Key
1. Log into your Recruitee account
2. Go to Settings → API
3. Generate a new API key
4. Copy the key to the GUI

#### Mistral API Key
1. Visit [Mistral AI](https://mistral.ai/)
2. Create an account and get API key
3. Copy the key to the GUI

### Application Settings

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| Company ID | Your Recruitee company identifier | 24899 | Any valid ID |
| Candidate Limit | Maximum candidates to process | 10 | 1-100 |
| Delay (seconds) | API call delay to prevent rate limiting | 2 | 1-60 |
| Upload to Recruitee | Enable/disable tag upload | Enabled | Boolean |
| Generate Excel | Create Excel output file | Enabled | Boolean |

### Configuration Persistence
- Settings are automatically saved to `cv_processing_settings.json`
- API keys are encrypted and stored locally
- Configuration persists between application restarts

## Usage Guide

### Step-by-Step Process

#### 1. Initial Setup
1. **Launch** the application
2. **Navigate** to Configuration tab
3. **Enter** your API keys
4. **Set** your company ID
5. **Configure** processing limits
6. **Save** configuration

#### 2. Processing Workflow
1. **Switch** to Processing tab
2. **Review** settings and options
3. **Click** "Start Processing"
4. **Monitor** progress in real-time
5. **Review** Excel output when complete
6. **Confirm** upload to Recruitee (if enabled)

#### 3. Results Review
1. **Open** generated Excel file
2. **Review** analysis results
3. **Verify** extracted information
4. **Proceed** with upload or adjust settings

### Processing Steps Explained

#### Step 1: CV Retrieval
- Connects to Recruitee API
- Searches for candidates without tags
- Respects configured candidate limit
- **Duration**: 30-60 seconds for 10 candidates

#### Step 2: CV Download
- Downloads PDF files from Recruitee
- Stores in local `downloaded_cvs/` folder
- Handles download errors gracefully
- **Duration**: 2-5 seconds per CV

#### Step 3: OCR Processing
- Converts PDF to text using Mistral OCR
- Handles various document formats
- Extracts structured text content
- **Duration**: 5-15 seconds per CV

#### Step 4: AI Analysis
- Analyzes extracted text with AI
- Identifies education, experience, skills
- Categorizes candidates automatically
- **Duration**: 10-30 seconds per CV

#### Step 5: Excel Generation
- Creates detailed Excel report
- Includes summary statistics
- Organizes data for easy review
- **Duration**: 5-10 seconds

#### Step 6: Recruitee Upload (Optional)
- Uploads structured tags to Recruitee
- Updates candidate profiles
- Provides upload confirmation
- **Duration**: 2-5 seconds per candidate

## Technical Documentation

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GUI Layer     │    │  Processing     │    │   API Layer     │
│   (PyQt6)       │<-->│   Thread        │<-->│  (Recruitee/    │
│                 │    │                 │    │   Mistral)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Configuration   │    │ File Management │    │ Error Handling  │
│ Management      │    │ (PDF/Excel)     │    │ & Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

#### 1. GUI Layer (`cv_processing_gui.py`)
- **Main Window**: Central application interface
- **Configuration Tab**: API keys and settings management
- **Processing Tab**: Workflow control and progress monitoring
- **Results Tab**: Statistics and output review

#### 2. Processing Thread (`ProcessingThread` class)
- **Multi-threaded**: Prevents GUI freezing
- **Signal-based**: Real-time progress updates
- **Error Recovery**: Automatic retry mechanisms
- **State Management**: Processing status tracking

#### 3. API Integration
- **Recruitee API**: Candidate retrieval and tag upload
- **Mistral API**: OCR processing and AI analysis
- **Rate Limiting**: Configurable delays between calls
- **Authentication**: Secure API key handling

#### 4. File Management
- **PDF Processing**: Download and OCR extraction
- **Excel Generation**: Structured output creation
- **Temporary Files**: Automatic cleanup
- **Data Persistence**: Configuration and results storage

### Data Flow

```
1. GUI Configuration -> API Keys & Settings
2. Start Processing -> Thread Initialization
3. Recruitee API -> Candidate List
4. PDF Download -> Local Storage
5. OCR Processing -> Text Extraction
6. AI Analysis -> Structured Data
7. Excel Generation -> Output File
8. Recruitee Upload -> Tag Updates
```

### Error Handling Strategy

#### Network Errors
- **Retry Logic**: Exponential backoff
- **Timeout Handling**: Configurable timeouts
- **Connection Recovery**: Automatic reconnection

#### File System Errors
- **Permission Handling**: User-friendly error messages
- **Disk Space**: Automatic cleanup and warnings
- **Path Issues**: Cross-platform path resolution

#### API Errors
- **Rate Limiting**: Automatic delay adjustment
- **Authentication**: Clear error messages
- **Data Validation**: Input sanitization

## API Integration

### Recruitee API

#### Endpoints Used
- `GET /c/{company_id}/candidates` - Retrieve candidates
- `GET /c/{company_id}/candidates/{id}/cv` - Download CV
- `POST /c/{company_id}/candidates/{id}/tags` - Upload tags

#### Authentication
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
```

#### Rate Limits
- **Requests per minute**: 60
- **Default delay**: 2 seconds
- **Configurable**: 1-60 seconds

### Mistral API

#### Services Used
- **OCR Processing**: PDF to text conversion
- **AI Analysis**: Content analysis and categorization

#### Authentication
```python
client = Mistral(api_key=api_key)
```

#### Rate Limits
- **Requests per minute**: 100
- **Default delay**: 2 seconds
- **Configurable**: 1-60 seconds

## Troubleshooting

### Common Issues

#### 1. "API Key Invalid" Error
**Symptoms**: Authentication failed messages
**Solutions**:
- Verify API key is correct
- Check key permissions
- Ensure no extra spaces
- Regenerate key if needed

#### 2. "No Candidates Found" Error
**Symptoms**: Empty candidate list
**Solutions**:
- Verify company ID is correct
- Check if candidates exist without tags
- Review API permissions
- Test API connection manually

#### 3. "OCR Processing Failed" Error
**Symptoms**: Text extraction errors
**Solutions**:
- Check Mistral API key
- Verify PDF file integrity
- Ensure sufficient API credits
- Review file size limits

#### 4. "Excel Generation Failed" Error
**Symptoms**: Output file creation errors
**Solutions**:
- Check disk space
- Verify write permissions
- Close Excel if file is open
- Check antivirus interference

#### 5. "Upload to Recruitee Failed" Error
**Symptoms**: Tag upload errors
**Solutions**:
- Verify Recruitee API key
- Check network connection
- Review candidate permissions
- Ensure tags are valid

### Performance Optimization

#### Slow Processing
- **Increase delay** between API calls
- **Reduce candidate limit** for testing
- **Check network speed**
- **Monitor system resources**

#### Memory Issues
- **Close other applications**
- **Process smaller batches**
- **Restart application**
- **Check available RAM**

### Debug Mode

#### Enable Console Output
```bash
# Edit cv_processing_gui.spec
console=True  # Change from False to True
```

#### View Logs
- Check application logs in output directory
- Review error messages in GUI
- Monitor network activity

## Deployment

### Building Executable

#### Automated Build
```bash
python build_exe.py
```

#### Manual Build
```bash
pyinstaller cv_processing_gui.spec
```

#### Build Options
- **One-file**: Single executable (larger, slower)
- **One-folder**: Executable + dependencies (recommended)
- **Console**: Include console window for debugging
- **Icon**: Custom application icon

### Distribution

#### Standalone Package
1. Build executable using PyInstaller
2. Test on clean machine
3. Create installer package
4. Distribute to users

#### Requirements
- Windows 10/11 (64-bit)
- No additional software needed
- Internet connection for API access

### Updates

#### Version Management
- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Backward compatibility**: Maintained where possible
- **Migration guides**: Provided for major updates

#### Distribution
- **Release notes**: Detailed change documentation
- **Migration scripts**: Automated configuration updates
- **Rollback support**: Previous version availability

## Contributing

### Development Setup
1. **Fork** the repository
2. **Create** feature branch
3. **Install** development dependencies
4. **Make** changes with tests
5. **Submit** pull request

### Code Standards
- **PEP 8**: Python style guide
- **Type hints**: Function signatures
- **Documentation**: Docstrings and comments
- **Testing**: Unit and integration tests

### Testing
```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=.

# Run GUI tests
python -m pytest tests/test_gui.py
```

## License

This project is licensed under the ORMIT TALENT & MARC VAN KAMPEN

# CV_TAG_2
