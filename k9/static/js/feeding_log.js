/**
 * Feeding Log Management Script
 * Handles CRUD operations for feeding log entries with Arabic RTL support
 */

class FeedingLogManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 50;
        this.deleteLogId = null;
        this.csrfToken = this.getCsrfToken();
        
        this.init();
    }

    init() {
        // Check if we're on the list page
        if (document.getElementById('feedingLogTable')) {
            this.initListPage();
        }
        
        // Check if we're on the form page  
        if (document.getElementById('feedingLogForm')) {
            this.initFormPage();
        }
    }

    initListPage() {
        console.log('Initializing feeding log list page...');
        
        // Load initial data
        this.loadFeedingLogs();
        this.loadFilterOptions();
        
        // Event listeners
        document.getElementById('applyFilters').addEventListener('click', () => {
            this.currentPage = 1;
            this.loadFeedingLogs();
        });
        
        document.getElementById('clearFilters').addEventListener('click', () => {
            this.clearFilters();
            this.currentPage = 1;
            this.loadFeedingLogs();
        });
        
        // Delete modal handling
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        document.getElementById('confirmDelete').addEventListener('click', () => {
            this.deleteFeedingLog(this.deleteLogId);
            deleteModal.hide();
        });
    }

    initFormPage() {
        console.log('Initializing feeding log form page...');
        
        const form = document.getElementById('feedingLogForm');
        const addSupplementBtn = document.getElementById('addSupplement');
        
        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });
        
        // Add supplement functionality
        addSupplementBtn.addEventListener('click', () => {
            this.addSupplementRow();
        });
        
        // Remove supplement functionality (delegated)
        document.getElementById('supplementsContainer').addEventListener('click', (e) => {
            if (e.target.closest('.remove-supplement')) {
                e.target.closest('.supplement-row').remove();
            }
        });
        
        // Validate meal type on change
        document.getElementById('meal_type_fresh').addEventListener('change', this.validateMealType);
        document.getElementById('meal_type_dry').addEventListener('change', this.validateMealType);
    }

    getCsrfToken() {
        // For now, we'll use an empty token since we're not using Flask-WTF CSRF
        // In a production environment, you would want to implement proper CSRF protection
        return '';
    }

    async loadFeedingLogs() {
        try {
            this.showLoading();
            
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage
            });
            
            // Add filters
            const projectId = document.getElementById('projectFilter').value;
            const dateFrom = document.getElementById('dateFromFilter').value;
            const dateTo = document.getElementById('dateToFilter').value;
            const dogId = document.getElementById('dogFilter').value;
            
            if (projectId) params.append('project_id', projectId);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            if (dogId) params.append('dog_id', dogId);
            
            const response = await fetch(`/api/breeding/feeding/log/list?${params}`, {
                credentials: 'include',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.updateKPIs(data.kpis);
            this.renderTable(data.items);
            this.renderPagination(data.pagination);
            
            this.hideLoading();
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading feeding logs:', error.message);
                this.showError('خطأ في تحميل سجلات التغذية');
            }
            this.hideLoading();
        }
    }

    async loadFilterOptions() {
        try {
            // Load projects for filter
            const projectsResponse = await fetch('/api/projects', {
                credentials: 'include',
                headers: { 'X-CSRFToken': this.csrfToken }
            });
            if (projectsResponse.ok) {
                const projectsData = await projectsResponse.json();
                // Ensure projectsData is an array
                if (Array.isArray(projectsData)) {
                    this.populateSelect('projectFilter', projectsData, 'id', 'name');
                } else {
                    console.error('Error loading projects: Expected array but got:', projectsData);
                    this.populateSelect('projectFilter', [], 'id', 'name');
                }
                
                // Add event listener for project change to update dogs
                const projectFilter = document.getElementById('projectFilter');
                if (projectFilter && !projectFilter.hasAttribute('data-listener-added')) {
                    projectFilter.addEventListener('change', () => {
                        this.updateDogFilter();
                    });
                    projectFilter.setAttribute('data-listener-added', 'true');
                }
            } else {
                console.error('Error loading projects:', await projectsResponse.text());
                this.populateSelect('projectFilter', [], 'id', 'name');
            }
            
            // Load dogs for filter (initially all dogs)
            await this.updateDogFilter();
            
        } catch (error) {
            console.error('Error loading filter options:', error);
            // Ensure selects are populated with empty arrays
            this.populateSelect('projectFilter', [], 'id', 'name');
            this.populateSelect('dogFilter', [], 'id', dog => `${dog.name} (${dog.code})`);
        }
    }

    async updateDogFilter() {
        try {
            const projectId = document.getElementById('projectFilter').value;
            const url = projectId ? `/api/dogs?project_id=${projectId}` : '/api/dogs';
            
            const dogsResponse = await fetch(url, {
                credentials: 'include',
                headers: { 'X-CSRFToken': this.csrfToken }
            });
            
            if (dogsResponse.ok) {
                const dogsData = await dogsResponse.json();
                // Ensure dogsData is an array before calling populateSelect
                if (Array.isArray(dogsData)) {
                    this.populateSelect('dogFilter', dogsData, 'id', dog => `${dog.name} (${dog.code})`);
                } else {
                    console.error('Error loading dogs: Expected array but got:', dogsData);
                    // Clear the select with empty array
                    this.populateSelect('dogFilter', [], 'id', dog => `${dog.name} (${dog.code})`);
                }
            } else {
                console.error('Error loading dogs:', await dogsResponse.text());
                // Clear the select with empty array
                this.populateSelect('dogFilter', [], 'id', dog => `${dog.name} (${dog.code})`);
            }
            
        } catch (error) {
            console.error('Error loading dogs:', error);
            // Clear the select with empty array
            this.populateSelect('dogFilter', [], 'id', dog => `${dog.name} (${dog.code})`);
        }
    }

    populateSelect(selectId, items, valueKey, textKey) {
        const select = document.getElementById(selectId);
        const currentValue = select.value;
        
        // Clear existing options except first
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueKey];
            option.textContent = typeof textKey === 'function' ? textKey(item) : item[textKey];
            select.appendChild(option);
        });
        
        // Restore selected value
        select.value = currentValue;
    }

    updateKPIs(kpis) {
        document.getElementById('totalRecords').textContent = kpis.total || 0;
        document.getElementById('totalGrams').textContent = `${kpis.grams_sum || 0} غم`;
        document.getElementById('totalWater').textContent = `${kpis.water_sum || 0} مل`;
        document.getElementById('totalSupplements').textContent = kpis.supplements_count || 0;
    }

    renderTable(items) {
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        
        if (items.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        items.forEach(item => {
            const row = this.createTableRow(item);
            tbody.appendChild(row);
        });
    }

    createTableRow(item) {
        const row = document.createElement('tr');
        
        // Format meal type display
        const mealTypes = [];
        if (item.meal_type_fresh) mealTypes.push('<span class="badge bg-success">طازج</span>');
        if (item.meal_type_dry) mealTypes.push('<span class="badge bg-warning">مجفف</span>');
        const mealTypeDisplay = mealTypes.join(' ');
        
        // Format supplements display - handle undefined properly
        const supplementsDisplay = item.supplements && Array.isArray(item.supplements) && item.supplements.length > 0 
            ? item.supplements.map(s => `${s.name || ''} (${s.qty || ''})`).join('، ')
            : 'لا يوجد';
        
        // Create row HTML (RTL order: Actions → Project → Dog → Notes → etc.)
        row.innerHTML = `
            <td>
                <div class="btn-group" role="group">
                    <a href="/breeding/feeding/log/${item.id}/edit" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="feedingLogManager.confirmDelete('${item.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
            <td>${item.project_name}</td>
            <td>${item.dog_name} (${item.dog_code})</td>
            <td><small class="text-muted">${item.notes || '-'}</small></td>
            <td>${item.body_condition || '-'}</td>
            <td><small>${supplementsDisplay}</small></td>
            <td class="text-center">${item.water_ml || '-'}</td>
            <td class="text-center">${item.grams || '-'}</td>
            <td>${item.prep_method || '-'}</td>
            <td>${item.meal_name || '-'}</td>
            <td>${mealTypeDisplay}</td>
            <td class="text-center">${item.time}</td>
            <td class="text-center">${this.formatDate(item.date)}</td>
        `;
        
        return row;
    }

    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        container.innerHTML = '';
        
        if (pagination.pages <= 1) {
            document.getElementById('paginationContainer').style.display = 'none';
            return;
        }
        
        document.getElementById('paginationContainer').style.display = 'block';
        
        // Previous button
        const prevDisabled = pagination.page <= 1;
        container.appendChild(this.createPaginationItem('السابق', pagination.page - 1, prevDisabled));
        
        // Page numbers
        for (let i = 1; i <= pagination.pages; i++) {
            const isActive = i === pagination.page;
            container.appendChild(this.createPaginationItem(i, i, false, isActive));
        }
        
        // Next button
        const nextDisabled = pagination.page >= pagination.pages;
        container.appendChild(this.createPaginationItem('التالي', pagination.page + 1, nextDisabled));
    }

    createPaginationItem(text, page, disabled = false, active = false) {
        const li = document.createElement('li');
        li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
        
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = text;
        
        if (!disabled) {
            a.addEventListener('click', (e) => {
                e.preventDefault();
                this.currentPage = page;
                this.loadFeedingLogs();
            });
        }
        
        li.appendChild(a);
        return li;
    }

    confirmDelete(logId) {
        this.deleteLogId = logId;
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    }

    async deleteFeedingLog(logId) {
        try {
            const response = await fetch(`/api/breeding/feeding/log/${logId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                this.loadFeedingLogs(); // Reload the list
            } else {
                this.showError(data.error || 'خطأ في حذف السجل');
            }
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error deleting feeding log:', error.message);
                this.showError('خطأ في حذف سجل التغذية');
            }
        }
    }

    clearFilters() {
        document.getElementById('projectFilter').value = '';
        document.getElementById('dateFromFilter').value = '';
        document.getElementById('dateToFilter').value = '';
        document.getElementById('dogFilter').value = '';
    }

    // Form page methods
    async handleFormSubmit() {
        if (!this.validateForm()) {
            return;
        }
        
        try {
            const formData = this.getFormData();
            const url = window.feedingLogData.isEdit 
                ? `/api/breeding/feeding/log/${window.feedingLogData.logId}`
                : '/api/breeding/feeding/log';
            const method = window.feedingLogData.isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                // Redirect to list page after success
                setTimeout(() => {
                    window.location.href = '/breeding/feeding/log';
                }, 1500);
            } else {
                this.showError(data.error || 'خطأ في حفظ البيانات');
            }
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error submitting form:', error.message);
                this.showError('خطأ في إرسال البيانات');
            }
        }
    }

    validateForm() {
        const form = document.getElementById('feedingLogForm');
        let isValid = true;
        
        // Clear previous validation
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        
        // Required fields validation
        const requiredFields = ['dog_id', 'date', 'time'];
        requiredFields.forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        // Meal type validation (at least one must be checked)
        const fresh = document.getElementById('meal_type_fresh').checked;
        const dry = document.getElementById('meal_type_dry').checked;
        
        if (!fresh && !dry) {
            document.getElementById('mealTypeError').style.display = 'block';
            isValid = false;
        } else {
            document.getElementById('mealTypeError').style.display = 'none';
        }
        
        return isValid;
    }

    validateMealType() {
        const fresh = document.getElementById('meal_type_fresh').checked;
        const dry = document.getElementById('meal_type_dry').checked;
        const errorDiv = document.getElementById('mealTypeError');
        
        if (!fresh && !dry) {
            errorDiv.style.display = 'block';
        } else {
            errorDiv.style.display = 'none';
        }
    }

    getFormData() {
        const form = document.getElementById('feedingLogForm');
        const formData = new FormData(form);
        
        // Convert FormData to JSON object
        const data = {};
        
        // Standard fields
        data.project_id = formData.get('project_id') || null;
        data.dog_id = formData.get('dog_id');
        data.date = formData.get('date');
        data.time = formData.get('time');
        data.meal_type_fresh = document.getElementById('meal_type_fresh').checked;
        data.meal_type_dry = document.getElementById('meal_type_dry').checked;
        data.meal_name = formData.get('meal_name') || null;
        data.prep_method = formData.get('prep_method') || null;
        data.body_condition = formData.get('body_condition') || null;
        data.notes = formData.get('notes') || null;
        
        // Numeric fields
        const grams = formData.get('grams');
        data.grams = grams ? parseInt(grams) : null;
        
        const waterMl = formData.get('water_ml');
        data.water_ml = waterMl ? parseInt(waterMl) : null;
        
        // Collect supplements
        const supplements = [];
        const supplementRows = document.querySelectorAll('.supplement-row');
        supplementRows.forEach(row => {
            const name = row.querySelector('[name="supplement_name"]').value.trim();
            const qty = row.querySelector('[name="supplement_qty"]').value.trim();
            if (name && qty) {
                supplements.push({ name, qty });
            }
        });
        data.supplements = supplements.length > 0 ? supplements : null;
        
        return data;
    }

    addSupplementRow() {
        const container = document.getElementById('supplementsContainer');
        const row = document.createElement('div');
        row.className = 'row supplement-row mb-2';
        row.innerHTML = `
            <div class="col-md-5">
                <input type="text" class="form-control" name="supplement_name" placeholder="اسم المكمل">
            </div>
            <div class="col-md-5">
                <input type="text" class="form-control" name="supplement_qty" placeholder="الكمية">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger btn-sm remove-supplement">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        container.appendChild(row);
    }

    // Utility methods
    formatDate(dateStr) {
        // Split the string to avoid timezone issues and format as DD/MM/YYYY
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    }

    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'block';
        document.getElementById('tableContainer').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'block';
    }

    showEmptyState() {
        document.getElementById('tableContainer').style.display = 'none';
        document.getElementById('emptyState').style.display = 'block';
        document.getElementById('paginationContainer').style.display = 'none';
    }

    hideEmptyState() {
        document.getElementById('emptyState').style.display = 'none';
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// Initialize the manager when the page loads
let feedingLogManager;
document.addEventListener('DOMContentLoaded', () => {
    feedingLogManager = new FeedingLogManager();
});