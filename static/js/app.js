// Ricky Application JavaScript

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Confirm delete actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Show loading spinner
function showLoading(element) {
    const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    if (element) {
        element.innerHTML = spinner;
        element.disabled = true;
    }
}

// Hide loading spinner
function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

// AJAX form submission
function submitFormAjax(formId, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('[type="submit"]');
        const originalText = submitButton.innerHTML;
        showLoading(submitButton);
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(submitButton, originalText);
            if (successCallback) {
                successCallback(data);
            }
        })
        .catch(error => {
            hideLoading(submitButton, originalText);
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    });
}

// Live search functionality
function setupLiveSearch(inputId, searchFunction) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    let timeout;
    input.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            searchFunction(input.value);
        }, 300);
    });
}

// Image preview on file select
function setupImagePreview(fileInputId, previewId) {
    const fileInput = document.getElementById(fileInputId);
    const preview = document.getElementById(previewId);
    
    if (!fileInput || !preview) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            preview.style.display = 'none';
        }
    });
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!', 'success');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    document.getElementById('toast-container').appendChild(toastElement.firstElementChild);
    
    const toast = new bootstrap.Toast(toastElement.firstElementChild);
    toast.show();
}

// Format datetime to relative time
function timeAgo(datetime) {
    const date = new Date(datetime);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
        }
    }
    
    return 'Just now';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
} 