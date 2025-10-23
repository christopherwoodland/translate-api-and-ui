# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability within this project, please follow responsible disclosure practices:

### Microsoft Security Response Center (MSRC)

Please report security vulnerabilities to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://msrc.microsoft.com/create-report).

Alternatively, you can email [secure@microsoft.com](mailto:secure@microsoft.com).

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: What an attacker could potentially do
- **Affected Components**: Which parts of the codebase are affected
- **Suggested Fix**: If you have ideas for how to fix it (optional)

### Response Timeline

- **Acknowledgment**: You'll receive an acknowledgment within 24-48 hours
- **Initial Assessment**: We'll provide an initial assessment within 1 week
- **Status Updates**: We'll keep you informed of progress
- **Resolution**: We'll work to patch the vulnerability as quickly as possible
- **Disclosure**: Once patched, we'll coordinate disclosure with you

## Security Best Practices

When using this project:

### Credential Management

- **Never commit credentials** to version control
- Store Azure credentials in environment variables or Azure Key Vault
- Use `.env` files locally (ensure `.gitignore` includes `.env`)
- Rotate credentials regularly

### Azure Managed Identity (Recommended for Production)

- Use Azure Managed Identity instead of access keys when possible
- Assign minimal required permissions (principle of least privilege)
- Enable Azure Managed Identity for Azure App Service, VMs, Container Apps

### Network Security

- Restrict storage account access using firewall rules
- Use private endpoints for Azure services when available
- Enable HTTPS-only for storage accounts
- Use Azure Virtual Networks for additional isolation

### Data Protection

- Enable encryption at rest for Azure Storage
- Use encrypted connections (HTTPS) for all API calls
- Be mindful of sensitive data in logs
- Consider data residency requirements for your region

### Access Control

- Use Azure RBAC (Role-Based Access Control)
- Assign minimum required roles:
  - Storage Blob Data Contributor for blob operations
  - Cognitive Services User for Translator API
- Review and audit access permissions regularly

### Monitoring and Auditing

- Enable Azure Storage logging
- Monitor for unusual access patterns
- Set up alerts for failed authentication attempts
- Review activity logs regularly

### Dependency Security

- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Review security advisories for Python packages
- Use `pip-audit` or similar tools to scan for vulnerabilities
- Pin dependency versions in `requirements.txt`

### Application Security

- Validate all user inputs
- Sanitize file names before processing
- Limit file upload sizes
- Implement rate limiting for the web UI
- Use CORS policies appropriately
- Enable CSRF protection for web forms

## Known Security Considerations

### Storage SAS Tokens

When using key-based authentication:
- SAS tokens are generated with short expiration times (1 hour default)
- SAS tokens have minimal required permissions (read/write for specific containers)
- Containers are created with unique names to prevent conflicts

### Logging

- The application logs translation operations to `translation_app.log`
- Logs do not include credentials or sensitive document content
- Review logs for any sensitive information before sharing

### Azure Services

This project uses Azure services that have their own security measures:
- **Azure Translator**: Managed by Microsoft, data encrypted in transit and at rest
- **Azure Storage**: Supports encryption, firewall rules, private endpoints
- **Azure Document Intelligence**: Processes documents securely, no data retention after processing

## Security Updates

We will publish security updates through:
- GitHub Security Advisories
- Release notes for patched versions
- Updates to this SECURITY.md file

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (with permission).

## Additional Resources

- [Azure Security Best Practices](https://learn.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)
- [Azure Storage Security Guide](https://learn.microsoft.com/azure/storage/common/storage-security-guide)
- [Azure Translator Security](https://learn.microsoft.com/azure/cognitive-services/translator/translator-security)
- [Microsoft Security Development Lifecycle](https://www.microsoft.com/securityengineering/sdl)

## Questions?

For security questions that are not vulnerabilities, please open an issue or contact [opencode@microsoft.com](mailto:opencode@microsoft.com).

---

Thank you for helping keep this project and its users safe!
