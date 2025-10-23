// Azure Document Translation UI - Main JavaScript

// State management
let selectedType = null;
let uploadedFiles = [];
let selectedLanguages = [];
let currentJobId = null;
let languages = [];

// DOM elements
const sections = {
    upload: document.getElementById('upload-section'),
    language: document.getElementById('language-section'),
    action: document.getElementById('action-section'),
    progress: document.getElementById('progress-section'),
    results: document.getElementById('results-section'),
    error: document.getElementById('error-section')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadLanguages();
    setupEventListeners();
});

// Load supported languages
async function loadLanguages() {
    try {
        const response = await fetch('/api/languages');
        languages = await response.json();
        renderLanguages();
        populateSourceLanguageDropdown();
    } catch (error) {
        console.error('Error loading languages:', error);
    }
}

// Populate source language dropdown
function populateSourceLanguageDropdown() {
    const dropdown = document.getElementById('source-language');
    languages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.code;
        option.textContent = `${lang.name} (${lang.code})`;
        dropdown.appendChild(option);
    });
}

// Render language options
function renderLanguages() {
    const grid = document.getElementById('language-grid');
    grid.innerHTML = '';
    
    languages.forEach(lang => {
        const option = document.createElement('div');
        option.className = 'language-option';
        option.dataset.code = lang.code;
        option.innerHTML = `
            <div class="language-name">${lang.name}</div>
            <div class="language-code">${lang.code}</div>
        `;
        option.addEventListener('click', () => toggleLanguage(lang.code));
        grid.appendChild(option);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Translation type selection
    document.querySelectorAll('.type-option').forEach(option => {
        option.addEventListener('click', () => selectType(option.dataset.type));
    });
    
    // File upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
    
    // Language search
    document.getElementById('language-search').addEventListener('input', (e) => {
        filterLanguages(e.target.value);
    });
    
    // Action buttons
    document.getElementById('start-btn').addEventListener('click', startTranslation);
    document.getElementById('reset-btn').addEventListener('click', resetForm);
}

// Select translation type
function selectType(type) {
    selectedType = type;
    
    // Update UI
    document.querySelectorAll('.type-option').forEach(option => {
        option.classList.remove('selected');
    });
    document.querySelector(`.type-option[data-type="${type}"]`).classList.add('selected');
    
    // Show next section
    sections.upload.style.display = 'block';
    
    // Update file input based on type
    const fileInput = document.getElementById('file-input');
    const fileLimitText = document.getElementById('file-limit-text');
    const languageLimitNotice = document.getElementById('language-limit-notice');
    const languageLimitText = document.getElementById('language-limit-text');
    
    if (type === 'single' || type === 'ocr') {
        fileInput.removeAttribute('multiple');
        fileLimitText.textContent = 'Select one document file (max 100MB)';
        languageLimitNotice.style.display = 'block';
        languageLimitText.textContent = 'Select exactly one target language';
    } else {
        fileInput.setAttribute('multiple', 'multiple');
        fileLimitText.textContent = 'Select multiple document files (max 100MB each)';
        languageLimitNotice.style.display = 'block';
        languageLimitText.textContent = 'Select one or more target languages';
    }
    
    // Clear previous selections
    uploadedFiles = [];
    selectedLanguages = [];
    updateFileList();
    updateLanguageSelection();
    updateStartButton();
}

// Handle file selection
function handleFiles(files) {
    // Allowed file extensions
    const allowedExtensions = [
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
        'odt', 'ods', 'odp', 'rtf', 'txt', 'html', 'htm',
        'mhtml', 'mht', 'md', 'markdown', 'mkdn', 'mdown', 'mdwn',
        'msg', 'xlf', 'xliff', 'csv', 'tsv', 'tab'
    ];
    
    const fileArray = Array.from(files).filter(file => {
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedExtensions.includes(extension);
    });
    
    if (fileArray.length === 0) {
        showError('Please select valid document files (PDF, Office, Text, etc.)');
        return;
    }
    
    // For single/ocr, only allow one file
    if ((selectedType === 'single' || selectedType === 'ocr') && uploadedFiles.length > 0) {
        uploadedFiles = [];
    }
    
    fileArray.forEach(file => {
        if (file.size > 100 * 1024 * 1024) {
            showError(`File ${file.name} exceeds 100MB limit`);
            return;
        }
        
        if ((selectedType === 'single' || selectedType === 'ocr') && uploadedFiles.length === 0) {
            uploadedFiles.push(file);
        } else if (selectedType === 'batch') {
            uploadedFiles.push(file);
        }
    });
    
    updateFileList();
    
    if (uploadedFiles.length > 0) {
        sections.language.style.display = 'block';
        sections.action.style.display = 'block';
    }
    
    updateStartButton();
}

// Get file icon based on extension
function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': '📕',
        'doc': '📘', 'docx': '📘',
        'xls': '📗', 'xlsx': '📗',
        'ppt': '📙', 'pptx': '📙',
        'odt': '📄', 'ods': '📊', 'odp': '📽️',
        'txt': '📝', 'rtf': '📝',
        'html': '🌐', 'htm': '🌐', 'mhtml': '🌐', 'mht': '🌐',
        'md': '📋', 'markdown': '📋', 'mkdn': '📋', 'mdown': '📋', 'mdwn': '📋',
        'msg': '📧',
        'xlf': '🌍', 'xliff': '🌍',
        'csv': '📊', 'tsv': '📊', 'tab': '📊'
    };
    return iconMap[extension] || '📄';
}

// Update file list display
function updateFileList() {
    const fileList = document.getElementById('file-list');
    
    if (uploadedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }
    
    fileList.innerHTML = uploadedFiles.map((file, index) => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-icon">${getFileIcon(file.name)}</div>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <span class="file-size">${formatFileSize(file.size)}</span>
                </div>
            </div>
            <button class="remove-file" onclick="removeFile(${index})">✕</button>
        </div>
    `).join('');
}

// Remove file from list
function removeFile(index) {
    uploadedFiles.splice(index, 1);
    updateFileList();
    updateStartButton();
    
    if (uploadedFiles.length === 0) {
        sections.language.style.display = 'none';
        sections.action.style.display = 'none';
    }
}

// Toggle language selection
function toggleLanguage(code) {
    const option = document.querySelector(`.language-option[data-code="${code}"]`);
    
    if (selectedType === 'single' || selectedType === 'ocr') {
        // Single selection
        selectedLanguages = [code];
        document.querySelectorAll('.language-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        option.classList.add('selected');
    } else {
        // Multiple selection
        if (selectedLanguages.includes(code)) {
            selectedLanguages = selectedLanguages.filter(l => l !== code);
            option.classList.remove('selected');
        } else {
            selectedLanguages.push(code);
            option.classList.add('selected');
        }
    }
    
    updateStartButton();
}

// Update language selection display
function updateLanguageSelection() {
    document.querySelectorAll('.language-option').forEach(opt => {
        opt.classList.remove('selected');
    });
}

// Filter languages by search
function filterLanguages(search) {
    const term = search.toLowerCase();
    document.querySelectorAll('.language-option').forEach(option => {
        const name = option.querySelector('.language-name').textContent.toLowerCase();
        const code = option.querySelector('.language-code').textContent.toLowerCase();
        
        if (name.includes(term) || code.includes(term)) {
            option.style.display = 'block';
        } else {
            option.style.display = 'none';
        }
    });
}

// Update start button state
function updateStartButton() {
    const startBtn = document.getElementById('start-btn');
    const canStart = uploadedFiles.length > 0 && selectedLanguages.length > 0;
    startBtn.disabled = !canStart;
}

// Start translation
async function startTranslation() {
    hideAllSections();
    sections.progress.style.display = 'block';
    
    try {
        // Upload files first
        updateProgress(0, 'Uploading files...');
        const formData = new FormData();
        uploadedFiles.forEach(file => formData.append('files', file));
        
        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error('File upload failed');
        }
        
        const uploadData = await uploadResponse.json();
        
        // Start translation job
        updateProgress(10, 'Starting translation job...');
        const sourceLanguage = document.getElementById('source-language').value;
        const translationResponse = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_type: selectedType,
                files: uploadData.files,
                target_languages: selectedLanguages,
                source_language: sourceLanguage || null
            })
        });
        
        if (!translationResponse.ok) {
            throw new Error('Failed to start translation');
        }
        
        const jobData = await translationResponse.json();
        currentJobId = jobData.job_id;
        
        // Poll for status
        pollJobStatus();
        
    } catch (error) {
        showError(error.message);
    }
}

// Poll job status
async function pollJobStatus() {
    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        const job = await response.json();
        
        updateProgress(job.progress, job.message);
        document.getElementById('progress-details').textContent = `Job ID: ${job.job_id} | Type: ${job.job_type}`;
        
        if (job.status === 'completed') {
            showResults(job);
        } else if (job.status === 'failed') {
            showError(job.error || 'Translation failed');
        } else {
            // Continue polling every 10 seconds
            setTimeout(pollJobStatus, 10000);
        }
        
    } catch (error) {
        showError('Error checking job status: ' + error.message);
    }
}

// Update progress display
function updateProgress(percent, message) {
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-text');
    
    fill.style.width = `${percent}%`;
    fill.textContent = `${percent}%`;
    text.textContent = message;
}

// Show results
function showResults(job) {
    hideAllSections();
    sections.results.style.display = 'block';
    
    const content = document.getElementById('results-content');
    
    // Debug: Log the job result to console
    console.log('Job Result:', job.result);
    console.log('Detected Source Language:', job.result.detected_source_language);
    
    // Helper function to get language name from code
    const getLanguageName = (code) => {
        const lang = languages.find(l => l.code === code);
        return lang ? lang.name : code;
    };
    
    // Build language detection info - always show it
    let languageInfo = '';
    const detectedLang = job.result.detected_source_language;
    const detectedLangs = job.result.detected_source_languages;
    
    // For single and OCR: show single detected language
    if (!detectedLangs) {
        if (!detectedLang || detectedLang === 'unknown') {
            // Show warning when language not detected
            languageInfo = `<div class="language-info language-info-warning">
                <strong>Source Language:</strong> Not available from API
            </div>`;
        } else if (detectedLang === 'auto-detected') {
            // Azure detected but doesn't expose the language code
            languageInfo = `<div class="language-info">
                <strong>Source Language:</strong> Auto-detected by Azure (language code not exposed by API)
            </div>`;
        } else {
            // Show detected language
            const sourceLangName = getLanguageName(detectedLang);
            languageInfo = `<div class="language-info">
                <strong>Source Language Detected:</strong> ${sourceLangName} (${detectedLang})
            </div>`;
        }
    }
    
    if (job.job_type === 'single') {
        const targetLangName = job.result.target_language ? getLanguageName(job.result.target_language) : '';
        content.innerHTML = `
            <div class="result-item">
                <h3>Translation Complete</h3>
                ${languageInfo}
                ${job.result.target_language ? `<div class="language-info"><strong>Target Language:</strong> ${targetLangName} (${job.result.target_language})</div>` : ''}
                <p>Your translated document is ready for download.</p>
                <a href="${job.result.download_url}" class="download-link" download>
                    📥 Download Translated PDF
                </a>
            </div>
        `;
    } else if (job.job_type === 'batch') {
        let html = '<div class="result-item">';
        html += '<h3>Batch Translation Complete</h3>';
        
        // Display detected source languages for each document
        if (detectedLangs && Object.keys(detectedLangs).length > 0) {
            html += '<div class="language-info">';
            html += '<strong>Source Languages:</strong><br>';
            Object.entries(detectedLangs).forEach(([filename, langCode]) => {
                if (langCode === 'auto-detected') {
                    html += `<span style="display: block; margin-left: 20px; margin-top: 5px;">• ${filename}: Auto-detected by Azure</span>`;
                } else if (langCode === 'unknown') {
                    html += `<span style="display: block; margin-left: 20px; margin-top: 5px;">• ${filename}: Not available</span>`;
                } else {
                    const langName = getLanguageName(langCode);
                    html += `<span style="display: block; margin-left: 20px; margin-top: 5px;">• ${filename}: ${langName} (${langCode})</span>`;
                }
            });
            html += '</div>';
        } else {
            html += languageInfo;
        }
        
        if (job.result.target_languages && job.result.target_languages.length > 0) {
            const targetNames = job.result.target_languages.map(code => getLanguageName(code)).join(', ');
            html += `<div class="language-info"><strong>Target Languages:</strong> ${targetNames}</div>`;
        }
        html += '<p>Your translated documents are ready for download.</p>';
        
        Object.entries(job.result.download_urls).forEach(([lang, urls]) => {
            const langName = getLanguageName(lang);
            html += `<h4>${langName} (${lang.toUpperCase()})</h4>`;
            urls.forEach(url => {
                const filename = url.split('/').pop();
                html += `<a href="${url}" class="download-link" download>📥 ${filename}</a>`;
            });
        });
        
        html += '</div>';
        content.innerHTML = html;
    } else if (job.job_type === 'ocr') {
        const targetLangName = job.result.target_language ? getLanguageName(job.result.target_language) : '';
        content.innerHTML = `
            <div class="result-item">
                <h3>OCR + Translation Complete</h3>
                ${languageInfo}
                ${job.result.target_language ? `<div class="language-info"><strong>Target Language:</strong> ${targetLangName} (${job.result.target_language})</div>` : ''}
                <p>Your documents are ready for download.</p>
                <a href="${job.result.download_urls.ocr_text}" class="download-link" download>
                    📄 Download OCR Text
                </a>
                <a href="${job.result.download_urls.searchable_pdf}" class="download-link" download>
                    📄 Download Searchable PDF
                </a>
                <a href="${job.result.download_urls.translated_pdf}" class="download-link" download>
                    📥 Download Translated PDF
                </a>
            </div>
        `;
    }
    
    content.innerHTML += `
        <div style="text-align: center; margin-top: 30px;">
            <button class="btn btn-primary" onclick="resetForm()">Start New Translation</button>
        </div>
    `;
}

// Show error
function showError(message) {
    hideAllSections();
    sections.error.style.display = 'block';
    document.getElementById('error-content').innerHTML = `
        <p><strong>Error:</strong> ${message}</p>
        <button class="btn btn-primary" onclick="resetForm()" style="margin-top: 20px;">Try Again</button>
    `;
}

// Reset form
function resetForm() {
    hideAllSections();
    selectedType = null;
    uploadedFiles = [];
    selectedLanguages = [];
    currentJobId = null;
    
    document.querySelectorAll('.type-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    updateFileList();
    updateLanguageSelection();
    document.getElementById('file-input').value = '';
    document.getElementById('language-search').value = '';
    renderLanguages();
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Hide all result sections
function hideAllSections() {
    Object.values(sections).forEach(section => {
        section.style.display = 'none';
    });
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
