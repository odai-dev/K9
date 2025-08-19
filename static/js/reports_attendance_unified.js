/**
 * Unified Attendance Matrix JavaScript
 * Handles filtering, AJAX calls, and dynamic table rendering
 */

let currentFilters = {};
let currentData = null;
let debounceTimer = null;

/**
 * Initialize the unified matrix interface
 */
function initializeUnifiedMatrix() {
    loadFilterOptions();
    setupEventListeners();
    setDefaultDates();
}

/**
 * Load filter options from API
 */
function loadFilterOptions() {
    // Load employees
    fetch('/api/employees')
        .then(response => response.json())
        .then(data => {
            const employeeSelect = document.getElementById('employee_ids');
            employeeSelect.innerHTML = '';
            
            if (data.employees) {
                data.employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = employee.name;
                    employeeSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.warn('Could not load employees:', error));
    
    // Load projects
    fetch('/api/projects')
        .then(response => response.json())
        .then(data => {
            const projectSelect = document.getElementById('project_ids');
            projectSelect.innerHTML = '';
            
            if (data.projects) {
                data.projects.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.id;
                    option.textContent = project.name;
                    projectSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.warn('Could not load projects:', error));
}

/**
 * Setup event listeners for form elements
 */
function setupEventListeners() {
    // Add debounced change listeners to form elements
    const form = document.getElementById('unified-filters-form');
    const inputs = form.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                // Auto-run if dates are filled
                const dateFrom = document.getElementById('date_from').value;
                const dateTo = document.getElementById('date_to').value;
                
                if (dateFrom && dateTo) {
                    runUnifiedMatrix();
                }
            }, 500);
        });
    });
}

/**
 * Set default date range (last 7 days)
 */
function setDefaultDates() {
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);
    
    document.getElementById('date_to').value = today.toISOString().split('T')[0];
    document.getElementById('date_from').value = weekAgo.toISOString().split('T')[0];
}

/**
 * Prefill filters from provided data
 */
function prefillFilters(data) {
    if (data.date_from) {
        document.getElementById('date_from').value = data.date_from;
    }
    if (data.date_to) {
        document.getElementById('date_to').value = data.date_to;
    }
    if (data.employee_ids && data.employee_ids.length > 0) {
        const employeeSelect = document.getElementById('employee_ids');
        data.employee_ids.forEach(id => {
            const option = employeeSelect.querySelector(`option[value="${id}"]`);
            if (option) option.selected = true;
        });
    }
    if (data.include_dogs) {
        document.getElementById('include_dogs').checked = data.include_dogs;
    }
}

/**
 * Run the unified matrix report
 */
function runUnifiedMatrix(page = 1) {
    const filters = collectFilters();
    filters.page = page;
    
    if (!validateFilters(filters)) {
        return;
    }
    
    currentFilters = filters;
    
    showLoading();
    hideError();
    
    fetch('/api/reports/attendance/run/unified', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        currentData = data;
        renderMatrix(data);
        renderLegend(data.legend);
        renderPagination(data.pagination);
        showExportButtons();
    })
    .catch(error => {
        hideLoading();
        showError('حدث خطأ في تحميل البيانات: ' + error.message);
        console.error('Error:', error);
    });
}

/**
 * Collect filter values from form
 */
function collectFilters() {
    const form = document.getElementById('unified-filters-form');
    const formData = new FormData(form);
    
    const filters = {
        date_from: formData.get('date_from'),
        date_to: formData.get('date_to'),
        employee_ids: formData.getAll('employee_ids'),
        project_ids: formData.getAll('project_ids'),
        shift_ids: formData.getAll('shift_ids'),
        include_dogs: formData.has('include_dogs'),
        status_in: formData.getAll('status_in'),
        per_page: parseInt(formData.get('per_page')) || 50
    };
    
    return filters;
}

/**
 * Validate filter values
 */
function validateFilters(filters) {
    if (!filters.date_from || !filters.date_to) {
        showError('يرجى تحديد نطاق التواريخ');
        return false;
    }
    
    const dateFrom = new Date(filters.date_from);
    const dateTo = new Date(filters.date_to);
    
    if (dateFrom > dateTo) {
        showError('تاريخ البداية يجب أن يكون قبل تاريخ النهاية');
        return false;
    }
    
    const daysDiff = (dateTo - dateFrom) / (1000 * 60 * 60 * 24);
    if (daysDiff > 62) {
        showError('نطاق التواريخ لا يمكن أن يتجاوز 62 يوماً');
        return false;
    }
    
    return true;
}

/**
 * Render the attendance matrix table
 */
function renderMatrix(data) {
    const headerRow = document.getElementById('header-row');
    const matrixBody = document.getElementById('matrix-body');
    
    // Clear existing content
    headerRow.innerHTML = '';
    matrixBody.innerHTML = '';
    
    if (!data.rows || data.rows.length === 0) {
        showNoData();
        return;
    }
    
    // Build header row
    const employeeHeader = document.createElement('th');
    employeeHeader.textContent = 'اسم الموظف';
    employeeHeader.className = 'employee-name table-sticky';
    headerRow.appendChild(employeeHeader);
    
    if (currentFilters.include_dogs) {
        const dogHeader = document.createElement('th');
        dogHeader.textContent = 'اسم الكلب';
        dogHeader.className = 'dog-name table-sticky';
        headerRow.appendChild(dogHeader);
    }
    
    // Add date headers in REVERSE order for RTL (newest dates on left)
    const days = [...data.days].reverse();
    days.forEach(day => {
        const dateHeader = document.createElement('th');
        const dateObj = new Date(day);
        const dayMonth = dateObj.toLocaleDateString('ar-SA', { 
            day: 'numeric', 
            month: 'numeric' 
        });
        dateHeader.textContent = dayMonth;
        dateHeader.className = 'date-header table-sticky';
        dateHeader.title = dateObj.toLocaleDateString('ar-SA', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        headerRow.appendChild(dateHeader);
    });
    
    // Build data rows
    data.rows.forEach(row => {
        const tr = document.createElement('tr');
        
        // Employee name
        const employeeCell = document.createElement('td');
        employeeCell.textContent = row.employee_name;
        employeeCell.className = 'employee-name';
        tr.appendChild(employeeCell);
        
        // Dog name if included
        if (currentFilters.include_dogs) {
            const dogCell = document.createElement('td');
            dogCell.textContent = row.dog_name || '';
            dogCell.className = 'dog-name';
            tr.appendChild(dogCell);
        }
        
        // Status cells in REVERSE order to match RTL header
        const cells = [...row.cells].reverse();
        cells.forEach(cell => {
            const statusCell = document.createElement('td');
            
            if (cell.status && !cell.project_controlled) {
                const badge = document.createElement('span');
                badge.className = `status-badge status-${cell.status}`;
                
                const statusLabels = {
                    'PRESENT': 'حاضر',
                    'ABSENT': 'غائب',
                    'LATE': 'متأخر',
                    'SICK': 'مرضية',
                    'LEAVE': 'إجازة',
                    'REMOTE': 'عن بُعد',
                    'OVERTIME': 'عمل إضافي'
                };
                
                badge.textContent = statusLabels[cell.status] || cell.status;
                badge.title = cell.tooltip;
                statusCell.appendChild(badge);
                
                // Add time info if available
                if (cell.check_in_time || cell.check_out_time) {
                    const timeInfo = document.createElement('div');
                    timeInfo.style.fontSize = '9px';
                    timeInfo.style.marginTop = '2px';
                    
                    if (cell.check_in_time && cell.check_out_time) {
                        timeInfo.textContent = `${cell.check_in_time}-${cell.check_out_time}`;
                    } else if (cell.check_in_time) {
                        timeInfo.textContent = cell.check_in_time;
                    }
                    
                    statusCell.appendChild(timeInfo);
                }
            } else if (cell.project_controlled) {
                // Project-controlled cells are blank per ownership rule
                statusCell.innerHTML = '<span class="text-muted" title="مستبعد من المصفوفة الموحدة">—</span>';
            }
            
            tr.appendChild(statusCell);
        });
        
        matrixBody.appendChild(tr);
    });
    
    showResults();
}

/**
 * Render the status legend
 */
function renderLegend(legend) {
    const legendDiv = document.getElementById('legend');
    legendDiv.innerHTML = '<strong>الدليل:</strong>';
    
    legend.forEach(item => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        
        const badge = document.createElement('span');
        badge.className = `status-badge status-${item.key}`;
        badge.textContent = item.label_ar;
        
        legendItem.appendChild(badge);
        legendDiv.appendChild(legendItem);
    });
    
    legendDiv.style.display = 'flex';
}

/**
 * Render pagination controls
 */
function renderPagination(pagination) {
    const paginationNav = document.getElementById('pagination-nav');
    const paginationUl = paginationNav.querySelector('.pagination');
    
    if (!paginationUl) return;
    
    paginationUl.innerHTML = '';
    
    if (pagination.pages <= 1) {
        paginationNav.style.display = 'none';
        return;
    }
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${pagination.page <= 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="window.runUnifiedMatrix(${pagination.page - 1})">السابق</a>`;
    paginationUl.appendChild(prevLi);
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === pagination.page ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#" onclick="window.runUnifiedMatrix(${i})">${i}</a>`;
        paginationUl.appendChild(pageLi);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${pagination.page >= pagination.pages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="window.runUnifiedMatrix(${pagination.page + 1})">التالي</a>`;
    paginationUl.appendChild(nextLi);
    
    paginationNav.style.display = 'block';
}

/**
 * Export matrix to specified format
 */
function exportMatrix(format) {
    if (!currentFilters) {
        showError('يرجى تشغيل التقرير أولاً');
        return;
    }
    
    const exportFilters = { ...currentFilters };
    // For export, get all pages
    exportFilters.page = 1;
    exportFilters.per_page = 1000;
    
    const endpoint = `/api/reports/attendance/export/${format}/unified`;
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportFilters)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Open the file
        if (data.path) {
            const fullPath = '/uploads/' + data.path;
            window.open(fullPath, '_blank');
        }
    })
    .catch(error => {
        showError('حدث خطأ في التصدير: ' + error.message);
        console.error('Export error:', error);
    });
}

/**
 * Reset filters to default values
 */
function resetFilters() {
    document.getElementById('unified-filters-form').reset();
    setDefaultDates();
    
    // Clear multi-selects
    document.getElementById('employee_ids').selectedIndex = -1;
    document.getElementById('project_ids').selectedIndex = -1;
    document.getElementById('shift_ids').selectedIndex = -1;
    
    // Reset checkboxes
    document.querySelectorAll('input[name="status_in"]').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    hideResults();
    hideError();
    document.getElementById('legend').style.display = 'none';
    document.getElementById('export-buttons').style.display = 'none';
}

/**
 * UI Helper Functions
 */
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    hideResults();
    hideNoData();
    hideError();
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showResults() {
    document.getElementById('results-container').style.display = 'block';
    hideNoData();
}

function hideResults() {
    document.getElementById('results-container').style.display = 'none';
}

function showNoData() {
    document.getElementById('no-data').style.display = 'block';
    hideResults();
}

function hideNoData() {
    document.getElementById('no-data').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}

function showExportButtons() {
    document.getElementById('export-buttons').style.display = 'block';
}

// Ensure all functions are globally accessible
window.runUnifiedMatrix = runUnifiedMatrix;
window.initializeUnifiedMatrix = initializeUnifiedMatrix;
window.resetFilters = resetFilters;
window.exportMatrix = exportMatrix;
window.prefillFilters = prefillFilters;

// Prevent default form submission
document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript file loaded successfully');
    console.log('runUnifiedMatrix available:', typeof runUnifiedMatrix === 'function');
    
    const form = document.getElementById('unified-filters-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            runUnifiedMatrix();
        });
    }
});