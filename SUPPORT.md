# Support

## How to Get Help

Thank you for using the Azure Document Translation project! This document provides guidance on how to get support.

## Documentation

First, check the comprehensive documentation in [README.md](README.md):

- **Quick Start Guide**: Step-by-step setup instructions
- **Usage Examples**: How to use all three translation modes
- **Troubleshooting**: Common issues and solutions
- **Configuration**: Detailed setup and customization options
- **Security**: Best practices for secure deployments

## Community Support

### GitHub Issues

For bugs, feature requests, or questions, please:

1. **Search existing issues** first to see if your question has been answered
2. **Open a new issue** if you don't find an answer
3. **Provide details**:
   - Operating system and Python version
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Error messages and logs (remove credentials!)
   - Screenshots if relevant

[Open an Issue →](https://github.com/christopherwoodland/translate-api-and-ui/issues)

### Discussions

For general questions, ideas, or community discussions:

- Use [GitHub Discussions](https://github.com/christopherwoodland/translate-api-and-ui/discussions) for Q&A
- Share your use cases and experiences
- Get help from the community

## Azure-Specific Support

### Azure Services

This project uses Azure services. For Azure-specific issues:

- **Azure Translator**: [Azure Translator Documentation](https://learn.microsoft.com/azure/cognitive-services/translator/)
- **Azure Document Intelligence**: [Document Intelligence Docs](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- **Azure Storage**: [Azure Storage Documentation](https://learn.microsoft.com/azure/storage/)

### Azure Support Plans

For production issues with Azure services, consider:

- [Azure Support Plans](https://azure.microsoft.com/support/plans/)
- [Azure Community Support](https://azure.microsoft.com/support/community/)
- [Microsoft Q&A](https://learn.microsoft.com/answers/topics/azure.html)

## Reporting Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

See [SECURITY.md](SECURITY.md) for instructions on reporting security vulnerabilities responsibly.

## Contributing

Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- How to submit pull requests
- Coding guidelines
- Development setup
- Testing procedures

## Common Issues

### Quick Solutions

Before opening an issue, try these common solutions:

**Authentication Errors:**
- Verify credentials in `.env` file
- Check Azure service endpoints are correct
- Ensure services are in the same region (recommended)

**Import Errors:**
- Reinstall dependencies: `pip install -r requirements.txt`
- Ensure you're using Python 3.8 or higher
- Activate your virtual environment

**Translation Failures:**
- Check supported file formats in README.md
- Verify file is not corrupted
- Check Azure service quotas and limits
- Review `translation_app.log` for detailed errors

**Web UI Issues:**
- Clear browser cache
- Try a different browser
- Check console for JavaScript errors
- Ensure Flask app is running on the correct port

## Feature Requests

We welcome feature ideas! When suggesting features:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** - why is this feature needed?
3. **Provide examples** of how it would work
4. **Consider alternatives** - are there workarounds?

## Response Time

Please note:
- This is an open-source project maintained by contributors
- Response times vary based on contributor availability
- Critical security issues are prioritized
- Community members often help answer questions faster

## Resources

### Official Documentation
- [Azure Translator API](https://learn.microsoft.com/azure/cognitive-services/translator/)
- [Azure Document Intelligence](https://learn.microsoft.com/azure/ai-services/document-intelligence/)
- [Azure Storage Blobs](https://learn.microsoft.com/azure/storage/blobs/)
- [Python Azure SDK](https://learn.microsoft.com/python/api/overview/azure/)

### Learning Resources
- [Azure Translation Tutorial](https://learn.microsoft.com/azure/cognitive-services/translator/quickstart-text-rest-api)
- [Azure Document Intelligence Tutorial](https://learn.microsoft.com/azure/ai-services/document-intelligence/quickstarts/get-started-sdks-rest-api)
- [Flask Documentation](https://flask.palletsprojects.com/)

### Community
- [Azure Community Forums](https://azure.microsoft.com/support/community/)
- [Microsoft Q&A - Azure Tag](https://learn.microsoft.com/answers/topics/azure.html)
- [Stack Overflow - Azure Tags](https://stackoverflow.com/questions/tagged/azure)

## Code of Conduct

This project follows the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Contact

For questions not covered here:
- Open a GitHub issue for project-specific questions
- Contact [opencode@microsoft.com](mailto:opencode@microsoft.com) for Microsoft-related inquiries

---

Thank you for being part of this project! Your feedback and contributions help make it better for everyone. 🙏
