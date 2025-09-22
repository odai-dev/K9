// Cleaning management JavaScript
let currentPage = 1;
let currentFilters = {};

// CSRF token
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('cleaningTableBody')) {
        initializeListPage();
    } else if (document.getElementById('cleaningForm')) {
        initializeFormPage();
    }
});

// List page initialization
function initializeListPage() {
    loadProjects();
    loadDogs();
    loadCleaningData();
    
    // Set up filter form submission
    document.getElementById('filterForm').addEventListener('submit', function(e) {
        e.preventDefault();
        applyFilters();
    });
    
    // Set default date range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    document.getElementById('dateTo').value = today.toISOString().split('T')[0];
    document.getElementById('dateFrom').value = thirtyDaysAgo.toISOString().split('T')[0];
}

// Form page initialization
function initializeFormPage() {
    setupMaterials();
    setupGroupDisinfectionValidation();
    
    // Set up form submission
    document.getElementById('cleaningForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm();
    });
}

// Load projects for filter
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const projects = await response.json();
        
        const projectSelect = document.getElementById('projectFilter');
        projectSelect.innerHTML = '<option value="">جميع المشاريع</option><option value="no_project">بدون مشروع</option>';
        
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            projectSelect.appendChild(option);
        });
        
        // Add event listener for project change to update dogs
        projectSelect.addEventListener('change', updateDogFilter);
    } catch (error) {
        if (error && error.message) {
            console.error('Error loading projects:', error.message);
        }
    }
}

// Load dogs for filter
async function loadDogs() {
    await updateDogFilter();
}

// Update dog filter based on selected project
async function updateDogFilter() {
    try {
        const projectId = document.getElementById('projectFilter').value;
        const url = projectId ? `/api/dogs?project_id=${projectId}` : '/api/dogs';
        
        // Use modern API client with authentication
        const params = projectId ? { project_id: projectId } : {};
        const response = await k9Api.getDogs(params);
        const dogs = response.data || response;
        
        const dogSelect = document.getElementById('dogFilter');
        dogSelect.innerHTML = '<option value="">جميع الكلاب</option>';
        
        dogs.forEach(dog => {
            const option = document.createElement('option');
            option.value = dog.id;
            option.textContent = dog.name;
            dogSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dogs:', error);
    }
}

// Apply filters and reload data
function applyFilters() {
    const form = document.getElementById('filterForm');
    const formData = new FormData(form);
    
    currentFilters = {};
    for (let [key, value] of formData.entries()) {
        if (value) {
            currentFilters[key] = value;
        }
    }
    
    currentPage = 1;
    loadCleaningData();
}

// Load cleaning data
async function loadCleaningData() {
    try {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 50,
            ...currentFilters
        });
        
        const response = await fetch(`/api/breeding/cleaning/list?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            updateKPIs(data.kpis);
            updateTable(data.items);
            updatePagination(data.pagination);
            showTable();
        } else {
            throw new Error(data.message || 'خطأ في تحميل البيانات');
        }
    } catch (error) {
        if (error && error.message) {
            console.error('Error loading cleaning data:', error.message);
            showError('خطأ في تحميل بيانات النظافة: ' + error.message);
        }
    }
}

// Update KPI cards
function updateKPIs(kpis) {
    document.getElementById('totalCount').textContent = kpis.total || 0;
    document.getElementById('cleanedCount').textContent = kpis.cleaned_yes || 0;
    document.getElementById('washedCount').textContent = kpis.washed_yes || 0;
    document.getElementById('disinfectedCount').textContent = kpis.disinfected_yes || 0;
    document.getElementById('dueWashCount').textContent = kpis.due_wash_count || 0;
    document.getElementById('dueDisinfectCount').textContent = kpis.due_disinfect_count || 0;
}

// Update table
function updateTable(items) {
    const tbody = document.getElementById('cleaningTableBody');
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editCleaning('${item.id}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteCleaning('${item.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
            <td>${item.project_name || ''}</td>
            <td>${item.dog_name || ''}</td>
            <td>${item.notes || ''}</td>
            <td>${formatMaterials(item.materials_used)}</td>
            <td>${item.group_description || ''}</td>
            <td>${formatYesNo(item.group_disinfection)}</td>
            <td>${formatYesNo(item.disinfected_house)}</td>
            <td>${formatYesNo(item.washed_house)}</td>
            <td>${formatYesNo(item.cleaned_house)}</td>
            <td>${item.alternate_place || ''}</td>
            <td>${item.cage_house_number || ''}</td>
            <td>${item.area_type || ''}</td>
            <td>${item.time || ''}</td>
            <td>${item.date || ''}</td>
        `;
        tbody.appendChild(row);
    });
}

// Format Yes/No values
function formatYesNo(value) {
    if (value === 'نعم') return '<span class="badge bg-success">نعم</span>';
    if (value === 'لا') return '<span class="badge bg-danger">لا</span>';
    return '<span class="text-muted">-</span>';
}

// Format materials
function formatMaterials(materials) {
    if (!materials || !Array.isArray(materials) || materials.length === 0) {
        return '<span class="text-muted">-</span>';
    }
    
    return materials.map(m => `${m.name} (${m.qty})`).join(', ');
}

// Update pagination
function updatePagination(pagination) {
    const container = document.getElementById('paginationContainer');
    const list = document.getElementById('paginationList');
    
    if (pagination.pages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    list.innerHTML = '';
    
    // Previous button
    if (pagination.has_prev) {
        list.innerHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${pagination.prev_num})">السابق</a></li>`;
    }
    
    // Page numbers
    for (let i = Math.max(1, pagination.page - 2); i <= Math.min(pagination.pages, pagination.page + 2); i++) {
        const active = i === pagination.page ? 'active' : '';
        list.innerHTML += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="changePage(${i})">${i}</a></li>`;
    }
    
    // Next button
    if (pagination.has_next) {
        list.innerHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${pagination.next_num})">التالي</a></li>`;
    }
}

// Change page
function changePage(page) {
    currentPage = page;
    loadCleaningData();
}

// Edit cleaning
function editCleaning(id) {
    window.location.href = `/breeding/cleaning/${id}/edit`;
}

// Delete cleaning
async function deleteCleaning(id) {
    if (!confirm('هل أنت متأكد من حذف هذا السجل؟')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/breeding/cleaning/${id}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        if (response.ok) {
            showSuccess('تم حذف السجل بنجاح');
            loadCleaningData();
        } else {
            const data = await response.json();
            throw new Error(data.message || 'خطأ في حذف السجل');
        }
    } catch (error) {
        if (error && error.message) {
            console.error('Error deleting cleaning:', error.message);
            showError('خطأ في حذف السجل: ' + error.message);
        }
    }
}

// Form functions
function setupMaterials() {
    const form = document.getElementById('cleaningForm');
    if (!form) return;
    
    // Initialize materials from existing data if editing
    const cleaningId = document.getElementById('cleaning_id')?.value;
    if (cleaningId) {
        // Load existing materials
        loadExistingMaterials(cleaningId);
    } else {
        // Add empty material row for new form
        addMaterialRow();
    }
}

function addMaterialRow(name = '', qty = '') {
    const container = document.getElementById('materialsContainer');
    const row = document.createElement('div');
    row.className = 'row mb-2 material-row';
    row.innerHTML = `
        <div class="col-md-5">
            <input type="text" class="form-control" name="material_name[]" placeholder="اسم المادة" value="${name}">
        </div>
        <div class="col-md-5">
            <input type="text" class="form-control" name="material_qty[]" placeholder="الكمية" value="${qty}">
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeMaterialRow(this)">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(row);
}

function removeMaterialRow(button) {
    button.closest('.material-row').remove();
}

function setupGroupDisinfectionValidation() {
    const groupDisinfection = document.getElementById('group_disinfection');
    const groupDescription = document.getElementById('group_description');
    
    if (groupDisinfection && groupDescription) {
        groupDisinfection.addEventListener('change', function() {
            if (this.value === 'نعم') {
                groupDescription.required = true;
                groupDescription.parentElement.querySelector('label').innerHTML = 
                    'وصف المجموعة <span class="text-danger">*</span>';
            } else {
                groupDescription.required = false;
                groupDescription.parentElement.querySelector('label').innerHTML = 'وصف المجموعة';
            }
        });
    }
}

// Submit form
async function submitForm() {
    try {
        const form = document.getElementById('cleaningForm');
        const formData = new FormData(form);
        
        // Collect materials
        const materialNames = formData.getAll('material_name[]');
        const materialQtys = formData.getAll('material_qty[]');
        const materials = [];
        
        for (let i = 0; i < materialNames.length; i++) {
            if (materialNames[i].trim() && materialQtys[i].trim()) {
                materials.push({
                    name: materialNames[i].trim(),
                    qty: materialQtys[i].trim()
                });
            }
        }
        
        // Build request data
        const data = {
            project_id: formData.get('project_id'),
            date: formData.get('date'),
            time: formData.get('time'),
            dog_id: formData.get('dog_id'),
            area_type: formData.get('area_type') || null,
            cage_house_number: formData.get('cage_house_number') || null,
            alternate_place: formData.get('alternate_place') || null,
            cleaned_house: formData.get('cleaned_house') || null,
            washed_house: formData.get('washed_house') || null,
            disinfected_house: formData.get('disinfected_house') || null,
            group_disinfection: formData.get('group_disinfection') || null,
            group_description: formData.get('group_description') || null,
            materials_used: materials.length > 0 ? materials : null,
            notes: formData.get('notes') || null
        };
        
        // Validate required fields (project_id is optional in some contexts)
        if (!data.date || !data.time || !data.dog_id) {
            throw new Error('يرجى ملء جميع الحقول المطلوبة');
        }
        
        // Validate group disinfection
        if (data.group_disinfection === 'نعم' && !data.group_description) {
            throw new Error('يرجى إدخال وصف المجموعة عند اختيار تطهير بيوت مجموعة كلاب');
        }
        
        // Validate at least one action
        if (!data.cleaned_house && !data.washed_house && !data.disinfected_house && 
            !data.group_disinfection && (!data.materials_used || data.materials_used.length === 0) && !data.notes) {
            throw new Error('يرجى تحديد إجراء واحد على الأقل أو إضافة ملاحظات');
        }
        
        // Determine if this is create or update
        const cleaningId = document.getElementById('cleaning_id')?.value;
        const url = cleaningId ? `/api/breeding/cleaning/${cleaningId}` : '/api/breeding/cleaning';
        const method = cleaningId ? 'PUT' : 'POST';
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add CSRF token if available
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch(url, {
            method: method,
            headers: headers,
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(cleaningId ? 'تم تحديث السجل بنجاح' : 'تم إضافة السجل بنجاح');
            setTimeout(() => {
                window.location.href = '/breeding/cleaning';
            }, 1500);
        } else {
            const errorMessage = result.error || result.message || 'خطأ في حفظ البيانات';
            console.error('Server error:', errorMessage);
            showError(errorMessage);
        }
    } catch (error) {
        console.error('Error submitting form:', error.message || error);
        showError(error.message || 'خطأ في حفظ البيانات');
    }
}

// Utility functions
function showLoading() {
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('tableContainer').style.display = 'none';
    document.getElementById('paginationContainer').style.display = 'none';
}

function showTable() {
    document.getElementById('loadingIndicator').style.display = 'none';
    document.getElementById('tableContainer').style.display = 'block';
}

function showSuccess(message) {
    // Create Bootstrap alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}

function showError(message) {
    // Create Bootstrap alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}