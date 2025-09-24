/**
 * Deworming Management JavaScript
 * Handles all deworming-related functionality including form submission, data loading, and UI interactions
 */

// Global variables
let currentPage = 1;
let currentFilters = {};

// Route name mappings in Arabic
const routeLabels = {
    'فموي': 'فموي',
    'موضعي': 'موضعي',
    'حقن': 'حقن'
};

const unitLabels = {
    'مل': 'مل',
    'ملغم': 'ملغم',
    'قرص': 'قرص'
};

const reactionLabels = {
    'لا يوجد': 'لا يوجد',
    'قيء': 'قيء',
    'إسهال': 'إسهال',
    'خمول': 'خمول',
    'تحسس جلدي': 'تحسس جلدي',
    'أخرى': 'أخرى'
};

// Initialize deworming functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the deworming list page
    if (document.getElementById('deworming-table')) {
        loadDewormingData();
        initializeFilters();
    }
    
    // Check if we're on the deworming form page
    if (document.getElementById('deworming-form')) {
        initializeDewormingForm();
    }
});

// Load deworming data for list page
function loadDewormingData(page = 1) {
    showLoading();
    
    const params = new URLSearchParams({
        page: page,
        per_page: 50,
        ...currentFilters
    });
    
    fetch(`/api/breeding/deworming/list?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            updateTable(data.items);
            updatePagination(data.pagination);
            updateKPIs(data.kpis);
            hideLoading();
        })
        .catch(error => {
            console.error('Error loading deworming data:', error.message);
            hideLoading();
            alert('خطأ في تحميل البيانات: ' + error.message);
        });
}

// Initialize filters
function initializeFilters() {
    // Project filter change
    const projectFilter = document.getElementById('project_filter');
    if (projectFilter) {
        projectFilter.addEventListener('change', function() {
            // Update dog filter based on selected project
            updateDogFilter();
        });
    }
}

// Update dog filter based on selected project
function updateDogFilter() {
    const projectId = document.getElementById('project_filter').value;
    const dogFilter = document.getElementById('dog_filter');
    
    if (!dogFilter) return;
    
    // Clear current options except "All Dogs"
    dogFilter.innerHTML = '<option value="">جميع الكلاب</option>';
    
    if (projectId) {
        // Load dogs for the selected project
        fetch(`/api/dogs?project_id=${projectId}`)
            .then(response => response.json())
            .then(data => {
                const dogs = data.data || data.dogs || data || []; // Handle different response formats
                if (Array.isArray(dogs)) {
                    dogs.forEach(dog => {
                    const option = document.createElement('option');
                    option.value = dog.id;
                    option.textContent = `${dog.name} (${dog.code})`;
                    dogFilter.appendChild(option);
                    });
                } else {
                    console.error('Expected dogs array but got:', typeof dogs, dogs);
                }
            })
            .catch(error => {
                console.error('Error loading dogs:', error);
            });
    } else {
        // Load all dogs when no project is selected
        fetch('/api/dogs')
            .then(response => response.json())
            .then(data => {
                const dogs = data.data || data.dogs || data || []; // Handle different response formats
                if (Array.isArray(dogs)) {
                    dogs.forEach(dog => {
                        const option = document.createElement('option');
                        option.value = dog.id;
                        option.textContent = `${dog.name} (${dog.code})`;
                        dogFilter.appendChild(option);
                    });
                } else {
                    console.error('Expected dogs array but got:', typeof dogs, dogs);
                }
            })
            .catch(error => {
                console.error('Error loading all dogs:', error);
            });
    }
}

// Apply filters
function applyFilters() {
    currentPage = 1;
    currentFilters = {
        project_id: document.getElementById('project_filter').value,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        dog_id: document.getElementById('dog_filter').value
    };
    loadDewormingData();
}

// Show loading spinner
function showLoading() {
    const spinner = document.getElementById('loading-spinner');
    const table = document.getElementById('deworming-table');
    const pagination = document.getElementById('pagination-nav');
    
    if (spinner) spinner.style.display = 'block';
    if (table) table.style.display = 'none';
    if (pagination) pagination.style.display = 'none';
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.getElementById('loading-spinner');
    const table = document.getElementById('deworming-table');
    
    if (spinner) spinner.style.display = 'none';
    if (table) table.style.display = 'table';
}

// Update table with deworming data
function updateTable(items) {
    const tbody = document.getElementById('deworming-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center text-muted">لا توجد بيانات متاحة</td></tr>';
        return;
    }
    
    items.forEach(item => {
        const row = document.createElement('tr');
        
        const dateTime = `${item.date} ${item.time}`;
        const weightDisplay = item.dog_weight_kg ? `${item.dog_weight_kg} كغ` : '-';
        const doseDisplay = item.calculated_dose_mg ? `${item.calculated_dose_mg} ملغ` : '-';
        const amountDisplay = item.administered_amount && item.amount_unit ? 
            `${item.administered_amount} ${unitLabels[item.amount_unit] || item.amount_unit}` : '-';
        const routeDisplay = item.administration_route ? 
            (routeLabels[item.administration_route] || item.administration_route) : '-';
        const reactionDisplay = item.adverse_reaction ? 
            (reactionLabels[item.adverse_reaction] || item.adverse_reaction) : '-';
        const nextDueDisplay = item.next_due_date || '-';
        
        row.innerHTML = `
            <td>${dateTime}</td>
            <td>${item.project_name}</td>
            <td>${item.dog_name} (${item.dog_code})</td>
            <td>${weightDisplay}</td>
            <td>${item.product_name || '-'}</td>
            <td>${item.active_ingredient || '-'}</td>
            <td>${doseDisplay}</td>
            <td>${amountDisplay}</td>
            <td>${routeDisplay}</td>
            <td>${reactionDisplay}</td>
            <td>${nextDueDisplay}</td>
            <td>
                <div class="btn-group" role="group">
                    <a href="/breeding/deworming/${item.id}/edit" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDeworming('${item.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update pagination
function updatePagination(pagination) {
    if (pagination.pages <= 1) {
        document.getElementById('pagination-nav').style.display = 'none';
        return;
    }
    
    document.getElementById('pagination-nav').style.display = 'block';
    const container = document.getElementById('pagination-container');
    container.innerHTML = '';
    
    // Previous button
    if (pagination.has_prev) {
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item';
        prevLi.innerHTML = `<a class="page-link" href="#" onclick="loadDewormingData(${pagination.prev_num})">السابق</a>`;
        container.appendChild(prevLi);
    }
    
    // Page numbers
    for (let i = 1; i <= pagination.pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === pagination.page ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="loadDewormingData(${i})">${i}</a>`;
        container.appendChild(li);
    }
    
    // Next button
    if (pagination.has_next) {
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item';
        nextLi.innerHTML = `<a class="page-link" href="#" onclick="loadDewormingData(${pagination.next_num})">التالي</a>`;
        container.appendChild(nextLi);
    }
}

// Update KPIs
function updateKPIs(kpis) {
    const elements = {
        'total-count': kpis.total || 0,
        'avg-mg-per-kg': kpis.avg_mg_per_kg || '0',
        'with-next-due': kpis.with_next_due || 0
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
    
    // Update route distribution
    const routeContainer = document.getElementById('route-distribution');
    if (routeContainer) {
        routeContainer.innerHTML = '';
        
        if (kpis.by_route && Object.keys(kpis.by_route).length > 0) {
            Object.entries(kpis.by_route).forEach(([route, count]) => {
                const routeLabel = routeLabels[route] || route;
                const badge = document.createElement('span');
                badge.className = 'badge bg-secondary me-2 mb-1';
                badge.textContent = `${routeLabel}: ${count}`;
                routeContainer.appendChild(badge);
            });
        } else {
            routeContainer.innerHTML = '<small class="text-muted">لا توجد بيانات</small>';
        }
    }
}

// Delete deworming record
function deleteDeworming(id) {
    if (!confirm('هل أنت متأكد من حذف هذا السجل؟')) {
        return;
    }
    
    fetch(`/api/breeding/deworming/${id}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        alert('تم حذف السجل بنجاح');
        loadDewormingData(currentPage);
    })
    .catch(error => {
        console.error('Error deleting deworming:', error.message);
        alert('خطأ في حذف السجل: ' + error.message);
    });
}

// Initialize deworming form
function initializeDewormingForm() {
    // Auto-calculate dose when weight or standard dose changes
    const weightInput = document.getElementById('dog_weight_kg');
    const standardDoseInput = document.getElementById('standard_dose_mg_per_kg');
    const calculatedDoseInput = document.getElementById('calculated_dose_mg');
    
    function calculateDose() {
        const weight = parseFloat(weightInput.value) || 0;
        const standardDose = parseFloat(standardDoseInput.value) || 0;
        
        if (weight > 0 && standardDose > 0) {
            const calculatedDose = (weight * standardDose).toFixed(1);
            calculatedDoseInput.value = calculatedDose;
        } else {
            calculatedDoseInput.value = '';
        }
    }
    
    if (weightInput) weightInput.addEventListener('input', calculateDose);
    if (standardDoseInput) standardDoseInput.addEventListener('input', calculateDose);
    
    // Form submission
    const form = document.getElementById('deworming-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

// Handle form submission
function handleFormSubmission(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Convert empty strings to null for optional fields
    Object.keys(data).forEach(key => {
        if (data[key] === '') {
            data[key] = null;
        }
    });
    
    const isEdit = document.getElementById('log_id');
    const url = isEdit ? `/api/breeding/deworming/${isEdit.value}` : '/api/breeding/deworming';
    const method = isEdit ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            throw new Error(result.error);
        }
        
        alert(isEdit ? 'تم تحديث السجل بنجاح' : 'تم إضافة السجل بنجاح');
        window.location.href = '/breeding/deworming';
    })
    .catch(error => {
        console.error('Error:', error.message);
        alert('خطأ في حفظ البيانات: ' + error.message);
    });
}