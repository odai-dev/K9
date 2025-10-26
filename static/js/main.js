// Main JavaScript for K9 Operations Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // Universal Search functionality
    initializeUniversalSearch();
});

// Universal Search
function initializeUniversalSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchModal = document.getElementById('searchModal');
    const searchInput = document.getElementById('universalSearchInput');
    const searchResults = document.getElementById('searchResults');

    if (!searchBtn || !searchModal || !searchInput) {
        return;
    }

    // Open modal and focus input
    searchBtn.addEventListener('click', function() {
        const modal = new bootstrap.Modal(searchModal);
        modal.show();
        setTimeout(() => searchInput.focus(), 300);
    });

    // Search on input with debounce
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.innerHTML = '<p class="text-muted text-center py-4">اكتب على الأقل حرفين للبحث</p>';
            return;
        }

        searchResults.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">جاري البحث...</span></div></div>';

        searchTimeout = setTimeout(async function() {
            try {
                const response = await apiClient.post('/api/search', { query: query });
                displaySearchResults(response);
            } catch (error) {
                searchResults.innerHTML = '<p class="text-danger text-center py-4">خطأ في البحث. حاول مرة أخرى.</p>';
            }
        }, 500);
    });
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    
    if (!results || Object.keys(results).length === 0) {
        searchResults.innerHTML = '<p class="text-muted text-center py-4">لا توجد نتائج</p>';
        return;
    }

    let html = '';
    
    // Display each category of results
    if (results.k9s && results.k9s.length > 0) {
        html += '<h6 class="text-muted mb-2">الكلاب</h6>';
        html += '<div class="list-group mb-3">';
        results.k9s.forEach(k9 => {
            html += `<a href="/k9s/${k9.id}" class="list-group-item list-group-item-action">
                <i class="fas fa-dog me-2"></i> ${k9.name} - ${k9.badge_number || ''}
            </a>`;
        });
        html += '</div>';
    }

    if (results.employees && results.employees.length > 0) {
        html += '<h6 class="text-muted mb-2">الموظفون</h6>';
        html += '<div class="list-group mb-3">';
        results.employees.forEach(emp => {
            html += `<a href="/employees/${emp.id}" class="list-group-item list-group-item-action">
                <i class="fas fa-user me-2"></i> ${emp.name} - ${emp.employee_id || ''}
            </a>`;
        });
        html += '</div>';
    }

    if (results.projects && results.projects.length > 0) {
        html += '<h6 class="text-muted mb-2">المشاريع</h6>';
        html += '<div class="list-group mb-3">';
        results.projects.forEach(proj => {
            html += `<a href="/projects/${proj.id}" class="list-group-item list-group-item-action">
                <i class="fas fa-project-diagram me-2"></i> ${proj.name}
            </a>`;
        });
        html += '</div>';
    }

    if (html === '') {
        html = '<p class="text-muted text-center py-4">لا توجد نتائج</p>';
    }

    searchResults.innerHTML = html;
}

// Dark mode toggle (if implemented)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Initialize dark mode from localStorage
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}
