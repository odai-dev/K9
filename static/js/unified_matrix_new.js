/**
 * Clean Unified Attendance Matrix JavaScript
 * Simple, working implementation
 */

// Global state
let matrixData = null;
let currentPage = 1;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Unified Matrix initialized');
    setupDateDefaults();
    setupEventHandlers();
});

// Set default date range (last 7 days)
function setupDateDefaults() {
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);
    
    document.getElementById('date_to').value = today.toISOString().split('T')[0];
    document.getElementById('date_from').value = weekAgo.toISOString().split('T')[0];
}

// Setup event handlers
function setupEventHandlers() {
    // Start report button
    const startBtn = document.getElementById('start-report-btn');
    if (startBtn) {
        startBtn.addEventListener('click', function() {
            console.log('Start report clicked');
            runReport();
        });
    }
    
    // Reset button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetForm();
        });
    }
    
    // Export buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('export-btn')) {
            const format = e.target.getAttribute('data-format');
            exportReport(format);
        }
    });
}

// Run the attendance matrix report
function runReport() {
    const dateFrom = document.getElementById('date_from').value;
    const dateTo = document.getElementById('date_to').value;
    
    if (!dateFrom || !dateTo) {
        showMessage('يرجى تحديد نطاق التواريخ', 'error');
        return;
    }
    
    const filters = {
        date_from: dateFrom,
        date_to: dateTo,
        page: currentPage,
        per_page: 50
    };
    
    showLoading();
    
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
            showMessage(data.error, 'error');
        } else {
            matrixData = data;
            displayResults(data);
            showExportButtons();
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('حدث خطأ في تحميل البيانات', 'error');
        console.error('Error:', error);
    });
}

// Display the results
function displayResults(data) {
    if (!data.rows || data.rows.length === 0) {
        showMessage('لا توجد بيانات للعرض', 'info');
        return;
    }
    
    const container = document.getElementById('results-container');
    const tableBody = document.getElementById('matrix-body');
    const headerRow = document.getElementById('header-row');
    
    // Clear previous results
    headerRow.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Build headers
    headerRow.innerHTML = '<th class="employee-name">الموظف</th>';
    if (data.headers) {
        data.headers.forEach(date => {
            headerRow.innerHTML += `<th class="date-header">${date}</th>`;
        });
    }
    
    // Build rows
    data.rows.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td class="employee-name">${row.employee_name}</td>`;
        
        if (row.attendance) {
            row.attendance.forEach(status => {
                const statusClass = status ? `status-${status}` : '';
                const statusText = getStatusText(status);
                tr.innerHTML += `<td><span class="status-badge ${statusClass}">${statusText}</span></td>`;
            });
        }
        
        tableBody.appendChild(tr);
    });
    
    container.style.display = 'block';
    document.getElementById('no-data').style.display = 'none';
}

// Get Arabic status text
function getStatusText(status) {
    const statusMap = {
        'PRESENT': 'حاضر',
        'ABSENT': 'غائب',
        'LATE': 'متأخر',
        'SICK': 'مرضية',
        'LEAVE': 'إجازة',
        'REMOTE': 'عن بُعد',
        'OVERTIME': 'إضافي'
    };
    return statusMap[status] || '-';
}

// Export report
function exportReport(format) {
    if (!matrixData) {
        showMessage('يرجى تشغيل التقرير أولاً', 'error');
        return;
    }
    
    const filters = {
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        page: 1,
        per_page: 1000
    };
    
    fetch(`/api/reports/attendance/export/${format}/unified`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showMessage(data.error, 'error');
        } else if (data.path) {
            window.open('/uploads/' + data.path, '_blank');
        }
    })
    .catch(error => {
        showMessage('حدث خطأ في التصدير', 'error');
        console.error('Export error:', error);
    });
}

// Reset form
function resetForm() {
    document.getElementById('unified-filters-form').reset();
    setupDateDefaults();
    hideResults();
    hideExportButtons();
    hideMessage();
}

// UI Helper functions
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    hideResults();
    hideMessage();
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showResults() {
    document.getElementById('results-container').style.display = 'block';
    document.getElementById('no-data').style.display = 'none';
}

function hideResults() {
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('no-data').style.display = 'block';
}

function showExportButtons() {
    document.getElementById('export-buttons').style.display = 'block';
}

function hideExportButtons() {
    document.getElementById('export-buttons').style.display = 'none';
}

function showMessage(message, type) {
    const messageDiv = document.getElementById('message-container');
    messageDiv.className = `alert alert-${type === 'error' ? 'danger' : type === 'info' ? 'info' : 'success'}`;
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
}

function hideMessage() {
    document.getElementById('message-container').style.display = 'none';
}