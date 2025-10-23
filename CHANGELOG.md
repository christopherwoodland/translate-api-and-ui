# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Microsoft Open Source compliance files
  - LICENSE (MIT)
  - CODE_OF_CONDUCT.md
  - CONTRIBUTING.md
  - SECURITY.md
  - SUPPORT.md
  - NOTICE
- GitHub issue templates (bug report, feature request)
- Pull request template
- CODEOWNERS file
- GitHub Actions workflow for Python linting
- Project badges in README.md

## [1.0.0] - 2025-10-23

### Added
- Initial release with comprehensive translation capabilities
- Web UI (Flask application) for document translation
- Single document translation script
- Batch translation script for multiple documents
- OCR + Translation pipeline for scanned documents
- Support for 25+ file formats:
  - PDF documents
  - Microsoft Office (Word, Excel, PowerPoint)
  - OpenDocument formats
  - Text files, HTML, Markdown
  - Email messages (.msg)
  - Localization files (.xlf, .xliff)
  - Data files (CSV, TSV)
  - Images (JPG, PNG, TIFF, BMP)
- Source language selection (100+ languages)
- Auto-detect source language
- Detected language display in results
- Real-time progress tracking
- Visual file type icons in UI
- Comprehensive logging with emoji indicators
- Azure Managed Identity support
- Smart download buttons with correct file types
- Container name validation
- Error handling and troubleshooting

### Features
- **Translation Modes**:
  - Single document translation
  - Batch translation (multiple files, multiple languages)
  - OCR + Translation (extract text from images/scans, then translate)
  
- **Authentication**:
  - Key-based authentication (development)
  - Azure Managed Identity (production)
  - Auto-detection of authentication method
  
- **Logging**:
  - Detailed logs in `translation_app.log`
  - Console output with emoji indicators
  - Per-document source language detection logging
  - Error messages with context
  
- **Web UI Features**:
  - Drag-and-drop file upload
  - Multiple file selection
  - Source language dropdown (100+ languages)
  - Target language selection
  - Real-time job status updates
  - Download translated files
  - Visual file type icons

### Documentation
- Comprehensive README.md with:
  - Quick start guide
  - Usage examples for all three modes
  - Troubleshooting section
  - Managed Identity setup instructions
  - Security best practices
  - Advanced configuration options

[Unreleased]: https://github.com/christopherwoodland/translate-api-and-ui/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/christopherwoodland/translate-api-and-ui/releases/tag/v1.0.0
