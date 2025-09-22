/**
 * Modern API Client for K9 Operations Management System
 * Handles authentication, error handling, and provides a unified interface
 */

class K9ApiClient {
    constructor() {
        this.baseUrl = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
        this.initCSRF();
    }

    /**
     * Initialize CSRF token from meta tag
     */
    initCSRF() {
        const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        if (csrfToken) {
            this.defaultHeaders['X-CSRFToken'] = csrfToken;
        }
    }

    /**
     * Make authenticated API request with proper error handling
     */
    async request(url, options = {}) {
        try {
            const config = {
                credentials: 'include', // Include session cookie
                headers: {
                    ...this.defaultHeaders,
                    ...options.headers
                },
                ...options
            };

            const response = await fetch(url, config);
            
            // Handle authentication redirects
            if (response.redirected && response.url.includes('/auth/login')) {
                throw new Error('Authentication required. Please log in again.');
            }

            // Handle HTTP errors
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const errorMessage = errorData?.error || errorData?.message || `HTTP ${response.status}: ${response.statusText}`;
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(url, params = {}) {
        const searchParams = new URLSearchParams(params);
        const queryString = searchParams.toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    /**
     * Download file with progress support
     */
    async downloadFile(url, filename = null) {
        try {
            const response = await fetch(url, {
                credentials: 'include',
                headers: this.defaultHeaders
            });

            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            // Extract filename from response headers or use provided name
            const finalFilename = filename || 
                response.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] ||
                'download';

            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = finalFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            return { success: true, filename: finalFilename };
        } catch (error) {
            console.error('Download Error:', error);
            throw error;
        }
    }

    // Specific API methods for common operations

    /**
     * Get dogs with filtering
     */
    async getDogs(filters = {}) {
        return this.get('/api/dogs', filters);
    }

    /**
     * Get dog by ID
     */
    async getDog(dogId) {
        return this.get(`/api/dogs/${dogId}`);
    }

    /**
     * Get employees with filtering
     */
    async getEmployees(filters = {}) {
        return this.get('/api/employees', filters);
    }

    /**
     * Get projects with filtering
     */
    async getProjects(filters = {}) {
        return this.get('/api/projects', filters);
    }

    /**
     * Generate report with modern progress handling
     */
    async generateReport(reportType, params = {}, format = 'pdf') {
        const reportData = {
            report_type: reportType,
            format: format,
            ...params
        };

        try {
            if (format === 'pdf') {
                return this.downloadFile(`/api/reports/${reportType}/pdf`, `${reportType}_report.pdf`);
            } else if (format === 'excel') {
                return this.downloadFile(`/api/reports/${reportType}/excel`, `${reportType}_report.xlsx`);
            } else {
                return this.post(`/api/reports/${reportType}`, reportData);
            }
        } catch (error) {
            throw new Error(`Report generation failed: ${error.message}`);
        }
    }
}

// Global instance
window.k9Api = new K9ApiClient();

/**
 * Show user-friendly error messages
 */
function showError(message, duration = 5000) {
    // Create or update error toast
    let errorToast = document.getElementById('error-toast');
    if (!errorToast) {
        errorToast = document.createElement('div');
        errorToast.id = 'error-toast';
        errorToast.className = 'alert alert-danger position-fixed';
        errorToast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(errorToast);
    }

    errorToast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-exclamation-circle me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.style.opacity='0'"></button>
        </div>
    `;

    // Show toast
    errorToast.style.opacity = '1';

    // Auto-hide after duration
    setTimeout(() => {
        errorToast.style.opacity = '0';
    }, duration);
}

/**
 * Show success messages
 */
function showSuccess(message, duration = 3000) {
    let successToast = document.getElementById('success-toast');
    if (!successToast) {
        successToast = document.createElement('div');
        successToast.id = 'success-toast';
        successToast.className = 'alert alert-success position-fixed';
        successToast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(successToast);
    }

    successToast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-check-circle me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.style.opacity='0'"></button>
        </div>
    `;

    successToast.style.opacity = '1';
    setTimeout(() => {
        successToast.style.opacity = '0';
    }, duration);
}

/**
 * Show loading indicator
 */
function showLoading(message = 'جاري التحميل...') {
    let loadingToast = document.getElementById('loading-toast');
    if (!loadingToast) {
        loadingToast = document.createElement('div');
        loadingToast.id = 'loading-toast';
        loadingToast.className = 'alert alert-info position-fixed';
        loadingToast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(loadingToast);
    }

    loadingToast.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
            <span>${message}</span>
        </div>
    `;

    loadingToast.style.opacity = '1';
    return loadingToast;
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingToast = document.getElementById('loading-toast');
    if (loadingToast) {
        loadingToast.style.opacity = '0';
    }
}

/**
 * Modern report generation with progress feedback
 */
async function generateModernReport(reportType, params = {}, format = 'pdf') {
    const loading = showLoading(`جاري إنشاء تقرير ${reportType}...`);
    
    try {
        const result = await k9Api.generateReport(reportType, params, format);
        hideLoading();
        showSuccess(`تم إنشاء التقرير بنجاح: ${result.filename}`);
        return result;
    } catch (error) {
        hideLoading();
        showError(`خطأ في إنشاء التقرير: ${error.message}`);
        throw error;
    }
}