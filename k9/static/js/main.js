// Main JavaScript file for K9 Operations Management System

// Global variables
let searchTimeout;
let searchModal;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeComponents();
    setupEventListeners();
    initializeModals();
});

// Theme Management
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    // Setup toggle listener
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
        } else {
            themeIcon.className = 'fas fa-moon';
        }
    }
}

// Initialize Bootstrap components and custom functionality
function initializeComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-permanent')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
    
    // Initialize search modal
    searchModal = new bootstrap.Modal(document.getElementById('searchModal'));
}

// Setup event listeners
function setupEventListeners() {
    // Global search functionality
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('input', handleGlobalSearch);
        searchInput.addEventListener('keydown', handleSearchKeydown);
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Dynamic form interactions
    setupDynamicFormInteractions();
    
    // Table enhancements
    enhanceTables();
    
    // Image preview functionality
    setupImagePreviews();
    
    // Auto-save functionality for forms (optional)
    setupAutoSave();
}

// Initialize modals
function initializeModals() {
    // Setup modal event listeners
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            // Focus first input in modal
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            // Clear form data when modal is closed
            const form = modal.querySelector('form');
            if (form && !form.classList.contains('no-reset')) {
                form.reset();
            }
        });
    });
}

// Global search functionality
function handleGlobalSearch(event) {
    const query = event.target.value.trim();
    
    // Clear previous timeout
    clearTimeout(searchTimeout);
    
    // Don't search if query is too short
    if (query.length < 2) {
        return;
    }
    
    // Debounce search requests
    searchTimeout = setTimeout(() => {
        performSearch(query);
    }, 300);
}

function handleSearchKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const query = event.target.value.trim();
        if (query.length >= 2) {
            performSearch(query);
        }
    }
}

function performSearch(query) {
    // Show loading state
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) {
        console.warn('Search input not found');
        return;
    }
    const originalPlaceholder = searchInput.placeholder;
    searchInput.placeholder = 'جاري البحث...';
    searchInput.classList.add('loading');
    
    // Make AJAX request
    fetch(`/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
            searchModal.show();
        })
        .catch(error => {
            if (error && error.message) {
                console.error('Search error:', error.message);
                showNotification('حدث خطأ أثناء البحث', 'error');
            }
        })
        .finally(() => {
            // Restore original state
            if (searchInput) {
                searchInput.placeholder = originalPlaceholder;
                searchInput.classList.remove('loading');
            }
        });
}

function displaySearchResults(data) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) {
        console.warn('Search results container not found');
        return;
    }
    let html = '';
    
    if (data.dogs.length === 0 && data.employees.length === 0 && (data.projects || []).length === 0) {
        html = '<div class="text-center py-4"><i class="fas fa-search fa-3x text-muted mb-3"></i><p class="text-muted">لم يتم العثور على نتائج</p><p class="text-sm text-muted">البحث شامل لجميع الكلاب والموظفين والمشاريع بدون قيود</p></div>';
    } else {
        // Dogs results - show more details
        if (data.dogs.length > 0) {
            html += '<h6 class="border-bottom pb-2 mb-3"><i class="fas fa-dog me-2"></i>الكلاب (' + data.dogs.length + ')</h6>';
            html += '<div class="row mb-4">';
            data.dogs.forEach(dog => {
                const statusBadge = dog.status === 'ACTIVE' ? 'success' : 'secondary';
                html += `
                    <div class="col-md-6 mb-2">
                        <a href="/dogs/${dog.id}" class="text-decoration-none">
                            <div class="search-result-item">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <strong>${dog.name}</strong>
                                        <small class="text-muted d-block">${dog.code}</small>
                                    </div>
                                    <span class="badge bg-${statusBadge} small">${dog.status || 'غير محدد'}</span>
                                </div>
                                <small class="text-muted">${dog.assigned_project || 'غير مُعين لمشروع'}</small>
                            </div>
                        </a>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        // Employees results - show role info
        if (data.employees.length > 0) {
            html += '<h6 class="border-bottom pb-2 mb-3"><i class="fas fa-users me-2"></i>الموظفين (' + data.employees.length + ')</h6>';
            html += '<div class="row mb-4">';
            data.employees.forEach(employee => {
                html += `
                    <div class="col-md-6 mb-2">
                        <a href="/employees/${employee.id}" class="text-decoration-none">
                            <div class="search-result-item">
                                <strong>${employee.name}</strong>
                                <small class="text-muted d-block">رقم: ${employee.employee_id}</small>
                                <small class="text-primary">${employee.role || 'غير محدد'}</small>
                            </div>
                        </a>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        // Projects results
        if (data.projects && data.projects.length > 0) {
            html += '<h6 class="border-bottom pb-2 mb-3"><i class="fas fa-project-diagram me-2"></i>المشاريع (' + data.projects.length + ')</h6>';
            html += '<div class="row">';
            data.projects.forEach(project => {
                const statusBadge = project.status === 'ACTIVE' ? 'success' : 
                                  project.status === 'PLANNED' ? 'warning' : 'secondary';
                html += `
                    <div class="col-md-6 mb-2">
                        <a href="/projects/${project.id}" class="text-decoration-none">
                            <div class="search-result-item">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <strong>${project.name}</strong>
                                        <small class="text-muted d-block">${project.code}</small>
                                    </div>
                                    <span class="badge bg-${statusBadge} small">${project.status || 'غير محدد'}</span>
                                </div>
                            </div>
                        </a>
                    </div>
                `;
            });
            html += '</div>';
        }
    }
    
    if (resultsContainer) {
        resultsContainer.innerHTML = html;
    }
}

// Form handling
function handleFormSubmit(event) {
    const form = event.target;
    
    // Add loading state to submit button
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';
        submitBtn.disabled = true;
        
        // Restore button after 2 seconds (in case form submission fails)
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 2000);
    }
    
    // Validate form
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        form.classList.add('was-validated');
        
        // Restore submit button
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
        
        // Show first validation error
        const firstInvalid = form.querySelector(':invalid');
        if (firstInvalid) {
            firstInvalid.focus();
            showNotification('يرجى تصحيح الأخطاء في النموذج', 'warning');
        }
        
        return false;
    }
    
    form.classList.add('was-validated');
}

// Dynamic form interactions
function setupDynamicFormInteractions() {
    // Auto-calculate expected delivery date in breeding forms
    const matingDateInput = document.querySelector('input[name="mating_date"]');
    const expectedDeliveryInput = document.querySelector('input[name="expected_delivery_date"]');
    
    if (matingDateInput && expectedDeliveryInput) {
        matingDateInput.addEventListener('change', function() {
            if (this.value) {
                const matingDate = new Date(this.value);
                const expectedDelivery = new Date(matingDate);
                expectedDelivery.setDate(expectedDelivery.getDate() + 63);
                expectedDeliveryInput.value = expectedDelivery.toISOString().split('T')[0];
            }
        });
    }
    
    // Password confirmation validation
    const passwordInput = document.querySelector('input[name="password"]');
    const confirmPasswordInput = document.querySelector('input[name="confirm_password"]');
    
    if (passwordInput && confirmPasswordInput) {
        function validatePasswords() {
            if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity('كلمات المرور غير متطابقة');
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        }
        
        passwordInput.addEventListener('input', validatePasswords);
        confirmPasswordInput.addEventListener('input', validatePasswords);
    }
    
    // Date range validation
    const startDateInputs = document.querySelectorAll('input[name="start_date"], input[name="session_date"], input[name="visit_date"]');
    const endDateInputs = document.querySelectorAll('input[name="end_date"], input[name="expected_completion_date"]');
    
    startDateInputs.forEach(startInput => {
        startInput.addEventListener('change', function() {
            endDateInputs.forEach(endInput => {
                if (this.value) {
                    endInput.min = this.value;
                    if (endInput.value && endInput.value < this.value) {
                        endInput.value = '';
                    }
                }
            });
        });
    });
}

// Table enhancements
function enhanceTables() {
    const tables = document.querySelectorAll('.table');
    
    tables.forEach(table => {
        // Add hover effects
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.01)';
                this.style.zIndex = '10';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
                this.style.zIndex = 'auto';
            });
        });
        
        // Add sorting functionality (basic)
        const headers = table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (!header.classList.contains('no-sort')) {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => sortTable(table, index));
            }
        });
    });
}

// Basic table sorting
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelectorAll('thead th')[columnIndex];
    
    // Determine sort direction
    const isAscending = !header.classList.contains('sort-desc');
    
    // Remove existing sort classes
    table.querySelectorAll('thead th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add new sort class
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue, 'ar') : 
            bValue.localeCompare(aValue, 'ar');
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// Image preview functionality
function setupImagePreviews() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create or update preview
                    let preview = document.getElementById(input.id + '_preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.id = input.id + '_preview';
                        preview.className = 'img-thumbnail mt-2';
                        preview.style.maxWidth = '200px';
                        preview.style.maxHeight = '200px';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

// Auto-save functionality (for long forms)
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-autosave]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                saveFormData(form);
            }, 1000));
        });
        
        // Load saved data on page load
        loadFormData(form);
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    const formId = form.id || form.action;
    localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
    
    // Show save indicator
    showNotification('تم حفظ البيانات تلقائياً', 'info', 2000);
}

function loadFormData(form) {
    const formId = form.id || form.action;
    const savedData = localStorage.getItem(`autosave_${formId}`);
    
    if (savedData) {
        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input && input.type !== 'file') {
                input.value = data[key];
            }
        });
    }
}

function clearSavedFormData(form) {
    const formId = form.id || form.action;
    localStorage.removeItem(`autosave_${formId}`);
}

// Utility functions
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

function showNotification(message, type = 'info', duration = 4000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        left: 20px;
        right: 20px;
        z-index: 9999;
        margin: 0 auto;
        max-width: 500px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            const bsAlert = new bootstrap.Alert(notification);
            bsAlert.close();
        }
    }, duration);
}

function formatDate(date, options = {}) {
    // Format as DD/MM/YYYY with standard numerals
    const dateObj = new Date(date);
    const day = String(dateObj.getDate()).padStart(2, '0');
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const year = dateObj.getFullYear();
    
    return `${day}/${month}/${year}`;
}

function formatTime(date, options = {}) {
    // Format as HH:MM with standard numerals
    const dateObj = new Date(date);
    const hours = String(dateObj.getHours()).padStart(2, '0');
    const minutes = String(dateObj.getMinutes()).padStart(2, '0');
    
    return `${hours}:${minutes}`;
}

function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Export functions for global use
window.K9System = {
    showNotification,
    formatDate,
    formatTime,
    validateForm,
    performSearch,
    debounce
};

// Add CSS for search results and other dynamic elements
const dynamicStyles = `
.search-result-item {
    padding: 0.75rem;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    background: #f8f9fa;
    transition: all 0.3s ease;
}

.search-result-item:hover {
    background: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.table th.sort-asc::after {
    content: ' ↑';
    color: #007bff;
}

.table th.sort-desc::after {
    content: ' ↓';
    color: #007bff;
}

.loading {
    opacity: 0.6;
    pointer-events: none;
}

.was-validated .form-control:invalid {
    border-color: #dc3545;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.was-validated .form-control:valid {
    border-color: #28a745;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
}

.img-thumbnail {
    border: 2px solid #e9ecef;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.img-thumbnail:hover {
    border-color: #007bff;
    transform: scale(1.05);
}

@media (max-width: 768px) {
    .position-fixed.alert {
        left: 10px !important;
        right: 10px !important;
        top: 10px !important;
    }
}
`;

// Inject dynamic styles
const styleSheet = document.createElement('style');
styleSheet.textContent = dynamicStyles;
document.head.appendChild(styleSheet);

// Page-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;
    
    // Dashboard specific functionality
    if (path === '/dashboard' || path === '/') {
        initializeDashboard();
    }
    
    // Reports page functionality
    if (path.includes('/reports')) {
        initializeReports();
    }
    
    // Forms page functionality
    if (document.querySelector('form')) {
        initializeFormHelpers();
    }
});

function initializeDashboard() {
    // Animate statistics cards
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        }, index * 100);
    });
}

function initializeReports() {
    // Add any reports-specific functionality here
    console.log('Reports page initialized');
}

function initializeFormHelpers() {
    // Add visual feedback for form interactions
    const inputs = document.querySelectorAll('.form-control, .form-select');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentNode.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentNode.classList.remove('focused');
        });
    });
}
