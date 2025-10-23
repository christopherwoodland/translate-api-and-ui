# Contributing to Azure Document Translation Project

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## How to Contribute

### Reporting Issues

- **Security vulnerabilities**: Please see [SECURITY.md](SECURITY.md) for reporting security issues
- **Bugs**: Open an issue describing the bug, including steps to reproduce
- **Feature requests**: Open an issue describing the feature and use case

When reporting issues, please include:
- Your operating system and Python version
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Any relevant error messages or logs

### Pull Requests

We welcome pull requests! Here's how to contribute code:

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding guidelines below
3. **Test your changes** thoroughly
4. **Update documentation** if needed (README.md, code comments)
5. **Submit a pull request** with a clear description of your changes

#### Pull Request Guidelines

- Keep pull requests focused on a single change
- Write clear, descriptive commit messages
- Reference any related issues in your PR description
- Ensure all existing tests pass
- Add tests for new functionality
- Update README.md if you're adding new features

### Coding Guidelines

#### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose
- Use type hints where appropriate

Example:
```python
def translate_document(input_file: str, target_language: str, source_language: str = None) -> dict:
    """
    Translate a document to a target language.
    
    Args:
        input_file: Path to the document to translate
        target_language: Target language code (e.g., 'es', 'fr')
        source_language: Optional source language code for auto-detection
        
    Returns:
        Dictionary containing translation results and metadata
    """
    pass
```

#### Code Organization

- Keep related functionality together
- Separate concerns (translation logic, file handling, API calls)
- Use helper functions to avoid code duplication
- Handle errors gracefully with informative messages

#### Logging

- Use the logging module instead of print statements
- Include context in log messages (job IDs, file names, etc.)
- Use appropriate log levels (INFO, WARNING, ERROR)
- Include emoji indicators for better readability (✓, →, ✗)

Example:
```python
logger.info(f"Job {job_id}: ✓ Source language detected: {source_lang}")
logger.error(f"Job {job_id}: ✗ Translation failed: {error_message}")
```

#### Error Handling

- Catch specific exceptions rather than broad try/except blocks
- Provide helpful error messages with context
- Log errors with full stack traces for debugging
- Clean up resources (close files, delete temp containers) on error

### Testing

Before submitting a pull request:

1. **Test locally** with your Azure credentials:
   - Single document translation
   - Batch translation
   - OCR + translation pipeline

2. **Test different file formats**:
   - PDF, Word, Excel, PowerPoint
   - Images (JPG, PNG, TIFF, BMP)
   - Text files, HTML, Markdown

3. **Test error scenarios**:
   - Invalid file formats
   - Missing credentials
   - Network errors
   - Invalid language codes

4. **Verify logging** output is clear and helpful

### Documentation

- Update README.md for new features or changed functionality
- Add code comments for complex logic
- Include docstrings for public functions and classes
- Update configuration examples if needed

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/christopherwoodland/translate-api-and-ui.git
cd translate-api-and-ui
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your `.env` file:
```bash
cp .env.template .env
# Edit .env with your Azure credentials
```

5. Test the application:
```bash
python app.py  # Start web UI
python single_document_translation.py  # Test single translation
```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test thoroughly
4. Commit: `git commit -m "Add feature: description"`
5. Push: `git push origin feature/your-feature-name`
6. Open a Pull Request on GitHub

## Questions?

- Open an issue for questions about the project
- Check existing issues to see if your question has been answered
- See [SUPPORT.md](SUPPORT.md) for support resources

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in release notes and project documentation.

Thank you for contributing! 🎉
