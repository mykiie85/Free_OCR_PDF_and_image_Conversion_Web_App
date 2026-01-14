// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // State management
    let selectedFiles = [];

    // DOM elements
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const selectedFilesContainer = document.getElementById('selectedFiles');
    const resultsSection = document.getElementById('resultsSection');
    const resultsContainer = document.getElementById('resultsContainer');
    const errorMessage = document.getElementById('errorMessage');

    // Constants
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
    const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'];

    // Check if all elements exist
    if (!uploadArea || !fileInput || !uploadForm || !submitBtn) {
        console.error('Required DOM elements not found');
        return;
    }

    // Event Listeners
    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleSubmit();
    });

    // Functions
    function handleFiles(files) {
        const filesArray = Array.from(files);
        
        for (const file of filesArray) {
            // Validate file
            const validation = validateFile(file);
            if (!validation.valid) {
                showError(validation.error);
                continue;
            }
            
            // Check if already added
            if (selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                continue;
            }
            
            selectedFiles.push(file);
        }
        
        updateSelectedFilesDisplay();
        hideError();
    }

    function validateFile(file) {
        // Check extension
        const extension = file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            return {
                valid: false,
                error: `Invalid file type: ${file.name}. Allowed types: ${ALLOWED_EXTENSIONS.join(', ')}`
            };
        }
        
        // Check size
        if (file.size > MAX_FILE_SIZE) {
            return {
                valid: false,
                error: `File too large: ${file.name}. Maximum size is 50MB.`
            };
        }
        
        return { valid: true };
    }

    function updateSelectedFilesDisplay() {
        if (selectedFiles.length === 0) {
            selectedFilesContainer.innerHTML = '';
            selectedFilesContainer.style.display = 'none';
            return;
        }
        
        selectedFilesContainer.style.display = 'block';
        selectedFilesContainer.innerHTML = selectedFiles.map((file, index) => `
            <div class="file-item">
                <div class="file-info">
                    <span class="file-icon">📄</span>
                    <div>
                        <div class="file-name">${escapeHtml(file.name)}</div>
                        <span class="file-size">${formatFileSize(file.size)}</span>
                    </div>
                </div>
                <button type="button" class="remove-file" onclick="window.removeFile(${index})">✕</button>
            </div>
        `).join('');
    }

    // Make removeFile available globally
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateSelectedFilesDisplay();
    };

    async function handleSubmit() {
        // Validate
        if (selectedFiles.length === 0) {
            showError('Please select at least one file to convert');
            return;
        }
        
        // Get format and language
        const format = document.querySelector('input[name="format"]:checked').value;
        const language = document.getElementById('languageSelect').value;
        
        // Prepare form data
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('format', format);
        formData.append('language', language);
        
        // Show loading
        setLoading(true);
        hideError();
        resultsSection.style.display = 'none';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }
            
            // Show results
            displayResults(data.results);
            
            // Clear selected files
            selectedFiles = [];
            updateSelectedFilesDisplay();
            fileInput.value = '';
            
        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(false);
        }
    }

    function displayResults(results) {
        resultsContainer.innerHTML = results.map(result => {
            if (result.success) {
                return `
                    <div class="result-item">
                        <div class="result-info">
                            <div class="result-filename">✓ ${escapeHtml(result.original_filename)}</div>
                            <div class="result-meta">${result.pages} page(s) • ${result.processing_time}s</div>
                        </div>
                        <a href="/download/${result.output_filename}" class="download-btn">
                            Download
                        </a>
                    </div>
                `;
            } else {
                return `
                    <div class="result-item error">
                        <div class="result-info">
                            <div class="result-filename">✗ ${escapeHtml(result.original_filename)}</div>
                            <div class="result-meta">${escapeHtml(result.error)}</div>
                        </div>
                    </div>
                `;
            }
        }).join('');
        
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function setLoading(loading) {
        submitBtn.disabled = loading;
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (loading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
        } else {
            btnText.style.display = 'block';
            btnLoader.style.display = 'none';
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});