/**
 * Grooming Management JavaScript
 * Handles list display, filtering, form submission, and CRUD operations
 */

// Global variables
let currentPage = 1;
let isLoading = false;
let deleteTargetId = null;

// CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('groomingTableBody')) {
        initializeGroomingList();
    }
    
    if (document.getElementById('groomingForm')) {
        initializeGroomingForm();
    }
});

// ============================================================
// LIST PAGE FUNCTIONALITY
// ============================================================

function initializeGroomingList() {
    // Load initial data
    loadGroomingLogs();
    
    // Set up event listeners
    document.getElementById('filtersForm').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1;
        loadGroomingLogs();
    });
    
    document.getElementById('clearFilters').addEventListener('click', function() {
        document.getElementById('filtersForm').reset();
        currentPage = 1;
        loadGroomingLogs();
    });
    
    // Set up delete modal
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    document.getElementById('confirmDelete').addEventListener('click', function() {
        if (deleteTargetId) {
            deleteGroomingLog(deleteTargetId);
            deleteModal.hide();
            deleteTargetId = null;
        }
    });
}

function loadGroomingLogs() {
    if (isLoading) return;
    isLoading = true;
    
    // Show loading spinner
    document.getElementById('groomingTableBody').innerHTML = `
        <tr>
            <td colspan="14" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">جاري التحميل...</span>
                </div>
            </td>
        </tr>
    `;
    
    // Build query parameters
    const params = new URLSearchParams({
        page: currentPage,
        per_page: 50
    });
    
    const projectId = document.getElementById('projectFilter').value;
    const dateFrom = document.getElementById('dateFromFilter').value;
    const dateTo = document.getElementById('dateToFilter').value;
    const dogId = document.getElementById('dogFilter').value;
    
    if (projectId) params.append('project_id', projectId);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    if (dogId) params.append('dog_id', dogId);
    
    // Fetch data
    fetch(`/api/breeding/grooming/list?${params}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
            return;
        }
        
        displayGroomingLogs(data.items);
        displayKPIs(data.kpis);
        displayPagination(data.pagination);
    })
    .catch(error => {
        console.error('Error loading grooming logs:', error);
        showAlert('error', 'خطأ في تحميل البيانات');
    })
    .finally(() => {
        isLoading = false;
    });
}

function displayGroomingLogs(logs) {
    const tbody = document.getElementById('groomingTableBody');
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="14" class="text-center text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i><br>
                    لا توجد سجلات عناية
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>
                <div class="btn-group" role="group">
                    <a href="/breeding/grooming/${log.id}/edit" class="btn btn-sm btn-outline-primary" title="تعديل">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="confirmDelete('${log.id}')" title="حذف">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
            <td><small>${log.project_name}</small></td>
            <td><small>${log.dog_name}</small></td>
            <td class="notes-cell" title="${log.notes}">${log.notes || '-'}</td>
            <td>
                ${log.cleanliness_score ? `<span class="badge bg-warning">${log.cleanliness_score}</span>` : '-'}
            </td>
            <td>
                ${log.eye_cleaning ? `<span class="badge ${log.eye_cleaning === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.eye_cleaning}</span>` : '-'}
            </td>
            <td>
                ${log.ear_cleaning ? `<span class="badge ${log.ear_cleaning === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.ear_cleaning}</span>` : '-'}
            </td>
            <td>
                ${log.teeth_brushing ? `<span class="badge ${log.teeth_brushing === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.teeth_brushing}</span>` : '-'}
            </td>
            <td>
                ${log.nail_trimming ? `<span class="badge ${log.nail_trimming === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.nail_trimming}</span>` : '-'}
            </td>
            <td>
                ${log.brushing ? `<span class="badge ${log.brushing === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.brushing}</span>` : '-'}
            </td>
            <td><small>${log.shampoo_type || '-'}</small></td>
            <td>
                ${log.washed_bathed ? `<span class="badge ${log.washed_bathed === 'نعم' ? 'bg-success' : 'bg-secondary'}">${log.washed_bathed}</span>` : '-'}
            </td>
            <td><small>${log.time}</small></td>
            <td><small>${log.date}</small></td>
        </tr>
    `).join('');
}

function displayKPIs(kpis) {
    const container = document.getElementById('kpisContainer');
    container.innerHTML = `
        <div class="d-flex flex-wrap justify-content-center">
            <div class="kpi-badge kpi-washed">
                <strong>${kpis.washed_yes}</strong> مغسول
            </div>
            <div class="kpi-badge kpi-brushed">
                <strong>${kpis.brushed_yes}</strong> تمشيط
            </div>
            <div class="kpi-badge kpi-nails">
                <strong>${kpis.nails_yes}</strong> قص أظافر
            </div>
            <div class="kpi-badge kpi-teeth">
                <strong>${kpis.teeth_yes}</strong> فرش أسنان
            </div>
            <div class="kpi-badge kpi-ear">
                <strong>${kpis.ear_yes}</strong> تنظيف أذن
            </div>
            <div class="kpi-badge kpi-eye">
                <strong>${kpis.eye_yes}</strong> تنظيف عين
            </div>
            <div class="kpi-badge kpi-cleanliness">
                متوسط النظافة: <strong>${kpis.avg_cleanliness}</strong>
            </div>
        </div>
        <small class="text-muted d-block mt-2">إجمالي السجلات: ${kpis.total}</small>
    `;
}

function displayPagination(pagination) {
    const container = document.getElementById('paginationContainer');
    const list = document.getElementById('paginationList');
    
    if (pagination.pages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    let paginationHTML = '';
    
    // Previous button
    if (pagination.page > 1) {
        paginationHTML += `<li class="page-item">
            <a class="page-link" href="#" onclick="changePage(${pagination.page - 1})">السابق</a>
        </li>`;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<li class="page-item ${i === pagination.page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
        </li>`;
    }
    
    // Next button
    if (pagination.page < pagination.pages) {
        paginationHTML += `<li class="page-item">
            <a class="page-link" href="#" onclick="changePage(${pagination.page + 1})">التالي</a>
        </li>`;
    }
    
    list.innerHTML = paginationHTML;
}

function changePage(page) {
    currentPage = page;
    loadGroomingLogs();
}

function confirmDelete(id) {
    deleteTargetId = id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

function deleteGroomingLog(id) {
    fetch(`/api/breeding/grooming/${id}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            loadGroomingLogs(); // Reload the list
        } else {
            showAlert('error', data.error || 'خطأ في حذف السجل');
        }
    })
    .catch(error => {
        console.error('Error deleting grooming log:', error);
        showAlert('error', 'خطأ في حذف السجل');
    });
}

// ============================================================
// FORM PAGE FUNCTIONALITY
// ============================================================

function initializeGroomingForm() {
    const form = document.getElementById('groomingForm');
    form.addEventListener('submit', handleFormSubmit);
    
    // Set default date and time if creating new record
    if (!document.getElementById('groomingId')) {
        const now = new Date();
        document.getElementById('date').value = now.toISOString().split('T')[0];
        document.getElementById('time').value = now.toTimeString().split(' ')[0].substring(0, 5);
    }
}

function initializeEditForm() {
    // This function is called from the template for edit forms
    // The form values are already populated by Jinja2 in the template
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    const groomingId = document.getElementById('groomingId')?.value;
    const isEdit = !!groomingId;
    
    // Collect form data
    const formData = {
        project_id: document.getElementById('projectId').value,
        date: document.getElementById('date').value,
        time: document.getElementById('time').value,
        dog_id: document.getElementById('dogId').value,
        recorder_employee_id: document.getElementById('recorderEmployeeId').value || null,
        shampoo_type: document.getElementById('shampooType').value,
        notes: document.getElementById('notes').value
    };
    
    // Collect radio button values
    const radioFields = [
        'washed_bathed', 'brushing', 'nail_trimming', 
        'teeth_brushing', 'ear_cleaning', 'eye_cleaning', 'cleanliness_score'
    ];
    
    radioFields.forEach(field => {
        const checked = document.querySelector(`input[name="${field}"]:checked`);
        formData[field] = checked ? checked.value : null;
    });
    
    // Validate required fields
    if (!formData.project_id || !formData.date || !formData.time || !formData.dog_id) {
        showAlert('error', 'يرجى ملء جميع الحقول المطلوبة');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('submitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';
    submitBtn.disabled = true;
    
    // Submit form
    const url = isEdit ? `/api/breeding/grooming/${groomingId}` : '/api/breeding/grooming';
    const method = isEdit ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', data.message);
            // Redirect to list page after short delay
            setTimeout(() => {
                window.location.href = '/breeding/grooming';
            }, 1000);
        } else {
            showAlert('error', data.error || 'خطأ في حفظ السجل');
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showAlert('error', 'خطأ في حفظ السجل');
    })
    .finally(() => {
        // Reset button state
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function showAlert(type, message) {
    // Try to use existing alert container first
    let alertContainer = document.getElementById('errorAlert');
    
    if (alertContainer) {
        const messageEl = document.getElementById('errorMessage');
        messageEl.textContent = message;
        
        // Update alert class
        alertContainer.className = `alert ${type === 'success' ? 'alert-success' : 'alert-danger'}`;
        alertContainer.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            alertContainer.style.display = 'none';
        }, 5000);
    } else {
        // Create temporary alert if no container exists
        const alert = document.createElement('div');
        alert.className = `alert ${type === 'success' ? 'alert-success' : 'alert-danger'} alert-dismissible`;
        alert.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of page
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alert, container.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Make functions available globally for onclick handlers
window.changePage = changePage;
window.confirmDelete = confirmDelete;
window.initializeEditForm = initializeEditForm;