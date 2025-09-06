/**
 * Excretion Management JavaScript
 * Handles both list and form functionality for excretion logs
 */

const ExcretionManager = {
    currentPage: 1,
    itemsPerPage: 50,
    currentFilters: {},
    deleteId: null,

    // Initialize list page
    initList() {
        this.loadProjects();
        this.loadDogs();
        this.bindListEvents();
        this.loadExcretionData();
    },

    // Initialize form page
    initForm(isEdit = false) {
        this.bindFormEvents();
        this.initFormValidation();
        
        if (isEdit) {
            // Form is pre-populated by the template
            console.log('Edit mode initialized');
        } else {
            // Set default date and time for new entries
            const now = new Date();
            const today = now.toISOString().split('T')[0];
            const currentTime = now.getHours().toString().padStart(2, '0') + ':' + 
                              now.getMinutes().toString().padStart(2, '0');
            
            document.getElementById('date').value = today;
            document.getElementById('time').value = currentTime;
        }
    },

    // Bind events for list page
    bindListEvents() {
        // Filter events
        const filterInputs = ['projectFilter', 'dogFilter', 'dateFrom', 'dateTo'];
        filterInputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.applyFilters());
            }
        });

        // Clear filters
        document.getElementById('clearFilters').addEventListener('click', () => {
            this.clearFilters();
        });

        // Delete confirmation
        document.getElementById('confirmDelete').addEventListener('click', () => {
            this.confirmDelete();
        });
    },

    // Bind events for form page
    bindFormEvents() {
        const form = document.getElementById('excretion-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('change', () => this.clearFieldError(input));
        });
    },

    // Load projects for dropdown
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                const projects = await response.json();
                const select = document.getElementById('projectFilter');
                if (select) {
                    select.innerHTML = '<option value="">جميع المشاريع</option><option value="no_project">بدون مشروع</option>';
                    projects.forEach(project => {
                        const option = document.createElement('option');
                        option.value = project.id;
                        option.textContent = project.name;
                        select.appendChild(option);
                    });
                    
                    // Add event listener for project change
                    select.addEventListener('change', () => this.updateDogFilter());
                }
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading projects:', error.message);
            }
        }
    },

    // Load dogs for dropdown
    async loadDogs() {
        await this.updateDogFilter();
    },

    // Update dog filter based on selected project
    async updateDogFilter() {
        try {
            const projectId = document.getElementById('projectFilter').value;
            const url = projectId ? `/api/dogs?project_id=${projectId}` : '/api/dogs';
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const dogs = await response.json();
            const select = document.getElementById('dogFilter');
            if (select) {
                select.innerHTML = '<option value="">جميع الكلاب</option>';
                dogs.forEach(dog => {
                    const option = document.createElement('option');
                    option.value = dog.id;
                    option.textContent = `${dog.name} - ${dog.code}`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading dogs:', error);
        }
    },

    // Apply filters and reload data
    applyFilters() {
        this.currentFilters = {
            project_id: document.getElementById('projectFilter').value,
            dog_id: document.getElementById('dogFilter').value,
            date_from: document.getElementById('dateFrom').value,
            date_to: document.getElementById('dateTo').value
        };
        
        this.currentPage = 1;
        this.loadExcretionData();
    },

    // Clear all filters
    clearFilters() {
        document.getElementById('projectFilter').value = '';
        document.getElementById('dogFilter').value = '';
        document.getElementById('dateFrom').value = '';
        document.getElementById('dateTo').value = '';
        
        this.currentFilters = {};
        this.currentPage = 1;
        this.loadExcretionData();
    },

    // Load excretion data from API
    async loadExcretionData() {
        this.showLoading(true);

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.itemsPerPage,
                ...this.currentFilters
            });

            const response = await fetch(`/api/breeding/excretion/list?${params}`);
            
            if (response.ok) {
                const data = await response.json();
                this.displayKPIs(data.kpis);
                this.displayData(data.items);
                this.displayPagination(data.pagination);
                
                if (data.items.length === 0) {
                    this.showNoData(true);
                } else {
                    this.showNoData(false);
                }
            } else {
                throw new Error('فشل في تحميل البيانات');
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading excretion data:', error.message);
                this.showError('حدث خطأ في تحميل البيانات');
            }
        } finally {
            this.showLoading(false);
        }
    },

    // Display KPI cards
    displayKPIs(kpis) {
        const container = document.getElementById('kpiCards');
        if (!container || !kpis) return;

        container.innerHTML = `
            <div class="col-md-3">
                <div class="kpi-card">
                    <h6>إجمالي السجلات</h6>
                    <p class="value">${kpis.total}</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <h6>حالات إمساك</h6>
                    <p class="value">${kpis.stool.constipation}</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <h6>براز غير طبيعي</h6>
                    <p class="value">${kpis.stool.abnormal_consistency}</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="kpi-card">
                    <h6>إجمالي القيء</h6>
                    <p class="value">${kpis.vomit.total_events}</p>
                </div>
            </div>
        `;
    },

    // Display data in table
    displayData(items) {
        const tbody = document.getElementById('dataTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/breeding/excretion/${item.id}/edit" class="btn btn-outline-primary btn-sm">
                            <i class="fas fa-edit"></i>
                        </a>
                        <button class="btn btn-outline-danger btn-sm" onclick="ExcretionManager.deleteItem('${item.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
                <td>${item.project_name || '-'}</td>
                <td>${item.dog_name || '-'} ${item.dog_code ? '(' + item.dog_code + ')' : ''}</td>
                <td>${item.vomit_notes || '-'}</td>
                <td>${item.vomit_count !== null ? item.vomit_count : '-'}</td>
                <td>${this.formatValue(item.vomit_color, 'badge-vomit')}</td>
                <td>${item.urine_notes || '-'}</td>
                <td>${this.formatValue(item.urine_color, 'badge-urine')}</td>
                <td>${item.stool_notes || '-'}</td>
                <td>${this.formatValue(item.stool_place, 'badge-normal')}</td>
                <td>${item.constipation ? '<span class="badge badge-constipation">نعم</span>' : '<span class="badge badge-normal">لا</span>'}</td>
                <td>${this.formatValue(item.stool_content, 'badge-stool')}</td>
                <td>${this.formatValue(item.stool_consistency, 'badge-stool')}</td>
                <td>${this.formatValue(item.stool_color, 'badge-stool')}</td>
                <td>${item.time}</td>
                <td>${item.date}</td>
            `;
            tbody.appendChild(row);
        });
    },

    // Format value with badge
    formatValue(value, badgeClass) {
        if (!value) return '-';
        return `<span class="badge ${badgeClass}">${value}</span>`;
    },

    // Display pagination
    displayPagination(pagination) {
        const container = document.getElementById('pagination');
        if (!container || !pagination) return;

        container.innerHTML = '';

        // Previous button
        if (pagination.page > 1) {
            container.appendChild(this.createPaginationButton(pagination.page - 1, 'السابق'));
        }

        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);

        for (let i = startPage; i <= endPage; i++) {
            const button = this.createPaginationButton(i, i.toString());
            if (i === pagination.page) {
                button.classList.add('active');
            }
            container.appendChild(button);
        }

        // Next button
        if (pagination.page < pagination.pages) {
            container.appendChild(this.createPaginationButton(pagination.page + 1, 'التالي'));
        }
    },

    // Create pagination button
    createPaginationButton(page, text) {
        const li = document.createElement('li');
        li.className = 'page-item';
        
        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = text;
        a.addEventListener('click', (e) => {
            e.preventDefault();
            this.currentPage = page;
            this.loadExcretionData();
        });
        
        li.appendChild(a);
        return li;
    },

    // Show/hide loading spinner
    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        if (spinner) {
            spinner.classList.toggle('d-none', !show);
        }
    },

    // Show/hide no data message
    showNoData(show) {
        const message = document.getElementById('noDataMessage');
        if (message) {
            message.classList.toggle('d-none', !show);
        }
    },

    // Show error message
    showError(message) {
        // You can implement a toast notification here
        alert(message);
    },

    // Delete item
    deleteItem(id) {
        this.deleteId = id;
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    },

    // Confirm delete
    async confirmDelete() {
        if (!this.deleteId) return;

        try {
            const response = await fetch(`/api/breeding/excretion/${this.deleteId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                // Hide modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                modal.hide();
                
                // Reload data
                this.loadExcretionData();
                
                // Show success message
                this.showSuccess('تم حذف السجل بنجاح');
            } else {
                throw new Error('فشل في حذف السجل');
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error deleting item:', error.message);
                this.showError('حدث خطأ في حذف السجل');
            }
        }

        this.deleteId = null;
    },

    // Handle form submission
    async handleFormSubmit(event) {
        event.preventDefault();

        if (!this.validateForm()) {
            return;
        }

        const submitBtn = document.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'جاري الحفظ...';

        try {
            const formData = this.getFormData();
            const isEdit = document.getElementById('excretion_id') !== null;
            
            const url = isEdit 
                ? `/api/breeding/excretion/${document.getElementById('excretion_id').value}`
                : '/api/breeding/excretion';
            
            const method = isEdit ? 'PUT' : 'POST';

            // Get CSRF token if needed
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const headers = {
                'Content-Type': 'application/json',
            };
            
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }

            const response = await fetch(url, {
                method: method,
                headers: headers,
                body: JSON.stringify(formData),
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess(result.message);
                // Redirect to list page after short delay
                setTimeout(() => {
                    window.location.href = '/breeding/excretion';
                }, 1500);
            } else {
                this.showFormErrors(result.error);
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error submitting form:', error.message);
                this.showError('حدث خطأ في حفظ البيانات');
            }
        } finally {
            // Hide loading state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    },

    // Get form data
    getFormData() {
        const form = document.getElementById('excretion-form');
        const formData = {};

        // Basic fields
        formData.project_id = form.project_id.value || null;
        formData.dog_id = form.dog_id.value;
        formData.date = form.date.value;
        formData.time = form.time.value;
        formData.recorder_employee_id = form.recorder_employee_id.value || null;

        // Stool fields
        formData.stool_color = form.stool_color.value || null;
        formData.stool_consistency = form.stool_consistency.value || null;
        formData.stool_content = form.stool_content.value || null;
        formData.constipation = form.constipation.checked;
        formData.stool_place = form.stool_place.value || null;
        formData.stool_notes = form.stool_notes.value || null;

        // Urine fields
        formData.urine_color = form.urine_color.value || null;
        formData.urine_notes = form.urine_notes.value || null;

        // Vomit fields
        formData.vomit_color = form.vomit_color.value || null;
        formData.vomit_count = form.vomit_count.value ? parseInt(form.vomit_count.value) : null;
        formData.vomit_notes = form.vomit_notes.value || null;

        return formData;
    },

    // Validate form
    validateForm() {
        let isValid = true;
        const form = document.getElementById('excretion-form');

        // Clear previous errors
        form.querySelectorAll('.validation-error').forEach(el => el.textContent = '');
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

        // Validate required fields (project_id is optional)
        const requiredFields = ['dog_id', 'date', 'time'];
        requiredFields.forEach(fieldName => {
            const field = form[fieldName];
            if (!field.value.trim()) {
                this.showFieldError(field, 'هذا الحقل مطلوب');
                isValid = false;
            }
        });

        // Validate at least one observation
        const hasStool = form.stool_color.value || form.stool_consistency.value || 
                        form.stool_content.value || form.constipation.checked || 
                        form.stool_place.value || form.stool_notes.value.trim();
                        
        const hasUrine = form.urine_color.value || form.urine_notes.value.trim();
        
        const hasVomit = form.vomit_color.value || form.vomit_count.value || 
                        form.vomit_notes.value.trim();

        if (!hasStool && !hasUrine && !hasVomit) {
            this.showError('يجب تسجيل ملاحظة واحدة على الأقل (براز أو بول أو قيء)');
            isValid = false;
        }

        // Validate vomit count
        if (form.vomit_count.value) {
            const count = parseInt(form.vomit_count.value);
            if (isNaN(count) || count < 0) {
                this.showFieldError(form.vomit_count, 'يجب أن يكون العدد >= 0');
                isValid = false;
            }
        }

        return isValid;
    },

    // Initialize form validation
    initFormValidation() {
        // Add any specific validation initialization here
    },

    // Validate individual field
    validateField(field) {
        this.clearFieldError(field);

        if (field.hasAttribute('required') && !field.value.trim()) {
            this.showFieldError(field, 'هذا الحقل مطلوب');
            return false;
        }

        return true;
    },

    // Show field error
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const errorElement = field.parentElement.querySelector('.validation-error');
        if (errorElement) {
            errorElement.textContent = message;
        }
    },

    // Clear field error
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorElement = field.parentElement.querySelector('.validation-error');
        if (errorElement) {
            errorElement.textContent = '';
        }
    },

    // Show form errors
    showFormErrors(error) {
        this.showError(error);
    },

    // Show success message
    showSuccess(message) {
        // You can implement a toast notification here
        alert(message);
    }
};

// Make ExcretionManager globally available
window.ExcretionManager = ExcretionManager;