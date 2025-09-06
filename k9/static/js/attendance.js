/**
 * Unified Global Attendance System - JavaScript Module
 * Handles client-side functionality for the attendance management interface
 */

class AttendanceManager {
    constructor() {
        this.currentDate = null;
        this.currentPage = 1;
        this.currentSearch = '';
        this.currentStatusFilter = '';
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
    }
    
    bindEvents() {
        // Main controls
        document.getElementById('load-attendance').addEventListener('click', () => {
            this.loadAttendanceData(1);
        });
        
        // Search on enter key
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadAttendanceData(1);
            }
        });
        
        // Date change
        document.getElementById('attendance-date').addEventListener('change', () => {
            this.loadAttendanceData(1);
        });
        
        // Status filter change
        document.getElementById('status-filter').addEventListener('change', () => {
            this.loadAttendanceData(1);
        });
        
        // Modal save button
        document.getElementById('save-attendance').addEventListener('click', () => {
            this.saveAttendance();
        });
    }
    
    loadInitialData() {
        // Load data for today by default
        this.loadAttendanceData(1);
        this.loadStatistics();
    }
    
    async loadAttendanceData(page = 1) {
        this.currentPage = page;
        this.currentDate = document.getElementById('attendance-date').value;
        this.currentSearch = document.getElementById('search-input').value.trim();
        this.currentStatusFilter = document.getElementById('status-filter').value;
        
        if (!this.currentDate) {
            this.showError('يرجى تحديد التاريخ');
            return;
        }
        
        this.showLoading(true);
        this.hideAllSections();
        
        try {
            const params = new URLSearchParams({
                date: this.currentDate,
                page: page.toString(),
                per_page: '20'
            });
            
            if (this.currentSearch) {
                params.append('search', this.currentSearch);
            }
            
            if (this.currentStatusFilter) {
                params.append('status', this.currentStatusFilter);
            }
            
            const response = await fetch(`/api/attendance?${params}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'خطأ في تحميل البيانات');
            }
            
            if (data.success) {
                this.renderAttendanceTable(data.employees);
                this.renderPagination(data.pagination);
                this.loadStatistics(); // Refresh stats
            } else {
                throw new Error(data.error || 'خطأ غير محدد');
            }
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading attendance data:', error.message);
                this.showError(error.message);
            }
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadStatistics() {
        try {
            const date = document.getElementById('attendance-date').value;
            if (!date) return;
            
            const response = await fetch(`/api/attendance/stats?date=${date}`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatistics(data.stats);
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading statistics:', error.message);
            }
        }
    }
    
    updateStatistics(stats) {
        document.getElementById('stat-present').textContent = stats.PRESENT || 0;
        document.getElementById('stat-absent').textContent = stats.ABSENT || 0;
        document.getElementById('stat-late').textContent = stats.LATE || 0;
        document.getElementById('stat-total').textContent = stats.total_editable || 0;
        
        // Show stats container
        document.getElementById('stats-container').style.display = 'flex';
    }
    
    renderAttendanceTable(employees) {
        const tbody = document.querySelector('#attendance-table tbody');
        tbody.innerHTML = '';
        
        if (employees.length === 0) {
            document.getElementById('empty-state').style.display = 'block';
            return;
        }
        
        employees.forEach(employee => {
            const row = this.createEmployeeRow(employee);
            tbody.appendChild(row);
        });
        
        document.getElementById('attendance-table-container').style.display = 'block';
    }
    
    createEmployeeRow(employee) {
        const row = document.createElement('tr');
        
        const statusBadge = this.getStatusBadge(employee.status);
        const roleArabic = this.getRoleArabic(employee.role);
        
        row.innerHTML = `
            <td>${employee.employee_id}</td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="me-2">
                        <i class="fas fa-user-circle text-muted"></i>
                    </div>
                    <div>
                        <div class="fw-medium">${employee.name}</div>
                    </div>
                </div>
            </td>
            <td>${roleArabic}</td>
            <td>${statusBadge}</td>
            <td>
                <small class="text-muted">${employee.note || ''}</small>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary edit-attendance-btn" 
                        data-employee-id="${employee.id}"
                        data-employee-name="${employee.name}"
                        data-status="${employee.status}"
                        data-note="${employee.note || ''}">
                    <i class="fas fa-edit me-1"></i>تعديل
                </button>
            </td>
        `;
        
        // Bind edit button event
        const editBtn = row.querySelector('.edit-attendance-btn');
        editBtn.addEventListener('click', () => this.openEditModal(editBtn));
        
        return row;
    }
    
    getStatusBadge(status) {
        const statusMap = {
            'PRESENT': { class: 'bg-success', text: 'حاضر', icon: 'check-circle' },
            'ABSENT': { class: 'bg-danger', text: 'غائب', icon: 'times-circle' },
            'LATE': { class: 'bg-warning', text: 'متأخر', icon: 'clock' },
            'SICK': { class: 'bg-secondary', text: 'مريض', icon: 'hospital' },
            'LEAVE': { class: 'bg-info', text: 'إجازة', icon: 'calendar' },
            'REMOTE': { class: 'bg-primary', text: 'عمل عن بعد', icon: 'home' },
            'OVERTIME': { class: 'bg-dark', text: 'عمل إضافي', icon: 'clock' }
        };
        
        const statusInfo = statusMap[status] || { class: 'bg-secondary', text: status, icon: 'question' };
        return `<span class="badge ${statusInfo.class}">
                    <i class="fas fa-${statusInfo.icon} me-1"></i>${statusInfo.text}
                </span>`;
    }
    
    getRoleArabic(role) {
        const roleMap = {
            'سائس': 'سائس',
            'مدرب': 'مدرب', 
            'مربي': 'مربي',
            'طبيب': 'طبيب',
            'مسؤول مشروع': 'مسؤول مشروع'
        };
        return roleMap[role] || role;
    }
    
    renderPagination(pagination) {
        const paginationContainer = document.getElementById('pagination');
        paginationContainer.innerHTML = '';
        
        if (pagination.pages <= 1) {
            document.getElementById('pagination-container').style.display = 'none';
            return;
        }
        
        document.getElementById('pagination-container').style.display = 'block';
        
        // Previous button
        const prevDisabled = pagination.page === 1 ? 'disabled' : '';
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${prevDisabled}`;
        prevLi.innerHTML = `<a class="page-link" href="#" data-page="${pagination.page - 1}">السابق</a>`;
        if (!prevDisabled) {
            prevLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.loadAttendanceData(pagination.page - 1);
            });
        }
        paginationContainer.appendChild(prevLi);
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${activeClass}`;
            pageLi.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            
            if (i !== pagination.page) {
                pageLi.querySelector('a').addEventListener('click', (e) => {
                    e.preventDefault();
                    this.loadAttendanceData(i);
                });
            }
            paginationContainer.appendChild(pageLi);
        }
        
        // Next button
        const nextDisabled = pagination.page === pagination.pages ? 'disabled' : '';
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${nextDisabled}`;
        nextLi.innerHTML = `<a class="page-link" href="#" data-page="${pagination.page + 1}">التالي</a>`;
        if (!nextDisabled) {
            nextLi.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.loadAttendanceData(pagination.page + 1);
            });
        }
        paginationContainer.appendChild(nextLi);
    }
    
    openEditModal(button) {
        const employeeId = button.dataset.employeeId;
        const employeeName = button.dataset.employeeName;
        const currentStatus = button.dataset.status;
        const currentNote = button.dataset.note;
        
        // Populate modal
        document.getElementById('employee-id').value = employeeId;
        document.getElementById('employee-name').value = employeeName;
        document.getElementById('attendance-date-display').value = this.currentDate;
        document.getElementById('attendance-status').value = currentStatus;
        document.getElementById('attendance-note').value = currentNote;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editAttendanceModal'));
        modal.show();
    }
    
    async saveAttendance() {
        const employeeId = document.getElementById('employee-id').value;
        const status = document.getElementById('attendance-status').value;
        const note = document.getElementById('attendance-note').value.trim();
        
        if (!employeeId || !status) {
            this.showError('يرجى ملء جميع الحقول المطلوبة');
            return;
        }
        
        const saveButton = document.getElementById('save-attendance');
        const originalText = saveButton.textContent;
        saveButton.disabled = true;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>جاري الحفظ...';
        
        try {
            const response = await fetch(`/api/attendance/${employeeId}?date=${this.currentDate}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    status: status,
                    note: note || null
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editAttendanceModal'));
                modal.hide();
                
                // Refresh data
                await this.loadAttendanceData(this.currentPage);
                
                this.showSuccess('تم حفظ الحضور بنجاح');
            } else if (response.status === 409) {
                // Project ownership conflict
                this.showError(data.error);
            } else {
                throw new Error(data.error || 'خطأ في حفظ البيانات');
            }
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error saving attendance:', error.message);
                this.showError(error.message);
            }
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = originalText;
        }
    }
    
    showLoading(show) {
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
    
    hideAllSections() {
        document.getElementById('attendance-table-container').style.display = 'none';
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('pagination-container').style.display = 'none';
    }
    
    showError(message) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of content
        const container = document.querySelector('.container-fluid');
        const firstChild = container.firstElementChild;
        container.insertBefore(alertDiv, firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    showSuccess(message) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of content
        const container = document.querySelector('.container-fluid');
        const firstChild = container.firstElementChild;
        container.insertBefore(alertDiv, firstChild);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AttendanceManager();
});