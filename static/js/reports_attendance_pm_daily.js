/**
 * PM Daily Report JavaScript
 * Handles UI interactions and API calls for PM Daily Reports
 */

class PMDailyReport {
    constructor() {
        this.projectSelect = document.getElementById('project-select');
        this.dateInput = document.getElementById('date-input');
        this.updateBtn = document.getElementById('update-btn');
        this.exportBtn = document.getElementById('export-btn');
        this.loading = document.getElementById('loading');
        this.errorDisplay = document.getElementById('error-display');
        this.errorMessage = document.getElementById('error-message');
        this.reportContent = document.getElementById('report-content');
        this.reportHeader = document.getElementById('report-header');
        this.reportTitle = document.getElementById('report-title');
        this.groupsContainer = document.getElementById('groups-container');
        this.specialRows = document.getElementById('special-rows-content');
        
        this.initializeEventListeners();
        this.loadReportIfParams();
    }
    
    initializeEventListeners() {
        this.updateBtn.addEventListener('click', () => this.updateReport());
        this.exportBtn.addEventListener('click', () => this.exportPDF());
        
        // Auto-update when filters change
        this.projectSelect.addEventListener('change', () => this.updateReport());
        this.dateInput.addEventListener('change', () => this.updateReport());
    }
    
    loadReportIfParams() {
        // If both project and date are set, load the report automatically
        if (this.projectSelect.value && this.dateInput.value) {
            this.updateReport();
        }
    }
    
    async updateReport() {
        const projectId = this.projectSelect.value;
        const date = this.dateInput.value;
        
        if (!projectId || !date) {
            this.showError('يرجى اختيار المشروع والتاريخ');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/reports/attendance/run/pm-daily', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId,
                    date: date
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'فشل في تحميل التقرير');
            }
            
            this.displayReport(data);
            this.exportBtn.disabled = false;
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error updating report:', error.message);
                this.showError(error.message || 'حدث خطأ في تحميل التقرير');
            }
        }
    }
    
    displayReport(data) {
        this.hideLoading();
        this.hideError();
        
        // Update header
        this.reportTitle.textContent = `اليوم: ${data.day_name_ar} - التاريخ: ${data.date}`;
        
        // Clear previous content
        this.groupsContainer.innerHTML = '';
        this.specialRows.innerHTML = '';
        
        // Display groups
        data.groups.forEach(group => {
            this.displayGroup(group);
        });
        
        // Display special rows
        this.displaySpecialRows(data.groups);
        
        this.reportContent.classList.remove('d-none');
    }
    
    displayGroup(group) {
        const template = document.getElementById('group-template');
        const groupElement = template.content.cloneNode(true);
        
        // Set group title
        const title = groupElement.querySelector('.group-title');
        title.textContent = `المجموعة ${group.group_no}`;
        
        const tbody = groupElement.querySelector('.group-body');
        
        // Add rows
        group.rows.forEach(row => {
            if (!row.is_on_leave_row && !row.is_replacement_row) {
                const rowElement = this.createRowElement(row);
                tbody.appendChild(rowElement);
            }
        });
        
        this.groupsContainer.appendChild(groupElement);
    }
    
    createRowElement(row) {
        const template = document.getElementById('row-template');
        const rowElement = template.content.cloneNode(true);
        const tr = rowElement.querySelector('tr');
        
        // Fill in data
        tr.querySelector('.employee-name').textContent = row.employee_name || '';
        tr.querySelector('.dog-name').textContent = row.dog_name || '';
        tr.querySelector('.site-name').textContent = row.site_name || '';
        tr.querySelector('.shift-name').textContent = row.shift_name || '';
        
        // Checkboxes
        tr.querySelector('.uniform-ok').textContent = row.uniform_ok ? '✓' : '';
        tr.querySelector('.card-ok').textContent = row.card_ok ? '✓' : '';
        tr.querySelector('.appearance-ok').textContent = row.appearance_ok ? '✓' : '';
        tr.querySelector('.cleanliness-ok').textContent = row.cleanliness_ok ? '✓' : '';
        tr.querySelector('.dog-exam-done').textContent = row.dog_exam_done ? '✓' : '';
        tr.querySelector('.dog-fed').textContent = row.dog_fed ? '✓' : '';
        tr.querySelector('.dog-watered').textContent = row.dog_watered ? '✓' : '';
        tr.querySelector('.training-tansheti').textContent = row.training_tansheti ? '✓' : '';
        tr.querySelector('.training-other').textContent = row.training_other ? '✓' : '';
        tr.querySelector('.field-deployment-done').textContent = row.field_deployment_done ? '✓' : '';
        
        // Performance evaluations
        tr.querySelector('.perf-sais').textContent = row.perf_sais || '';
        tr.querySelector('.perf-dog').textContent = row.perf_dog || '';
        tr.querySelector('.perf-murabbi').textContent = row.perf_murabbi || '';
        tr.querySelector('.perf-sehi').textContent = row.perf_sehi || '';
        tr.querySelector('.perf-mudarrib').textContent = row.perf_mudarrib || '';
        
        // Violations
        tr.querySelector('.violations').textContent = row.violations || '';
        
        return rowElement;
    }
    
    displaySpecialRows(groups) {
        const specialRows = [];
        
        // Collect special rows from all groups
        groups.forEach(group => {
            group.rows.forEach(row => {
                if (row.is_on_leave_row || row.is_replacement_row) {
                    specialRows.push(row);
                }
            });
        });
        
        // Display special rows
        specialRows.forEach(row => {
            this.displaySpecialRow(row);
        });
    }
    
    displaySpecialRow(row) {
        const template = document.getElementById('special-row-template');
        const element = template.content.cloneNode(true);
        
        if (row.is_on_leave_row) {
            element.querySelector('.special-type').textContent = 'الفرد المأجز';
            element.querySelector('.special-employee').textContent = row.on_leave_employee_name || '';
            element.querySelector('.special-dog').textContent = row.on_leave_dog_name || '';
            element.querySelector('.special-leave-type').textContent = row.on_leave_type || '';
            element.querySelector('.special-note').textContent = row.on_leave_note || '';
        } else if (row.is_replacement_row) {
            element.querySelector('.special-type').textContent = 'الفرد البديل';
            element.querySelector('.special-employee').textContent = row.replacement_employee_name || '';
            element.querySelector('.special-dog').textContent = row.replacement_dog_name || '';
            element.querySelector('.special-leave-type').textContent = '';
            element.querySelector('.special-note').textContent = '';
        }
        
        this.specialRows.appendChild(element);
    }
    
    async exportPDF() {
        const projectId = this.projectSelect.value;
        const date = this.dateInput.value;
        
        if (!projectId || !date) {
            this.showError('يرجى اختيار المشروع والتاريخ');
            return;
        }
        
        this.exportBtn.disabled = true;
        this.exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin ml-1"></i> جاري التصدير...';
        
        try {
            const response = await fetch('/api/reports/attendance/export/pdf/pm-daily', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId,
                    date: date
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'فشل في تصدير PDF');
            }
            
            // Open/download the PDF
            window.open('/' + data.path, '_blank');
            
        } catch (error) {
            if (error && error.message) {
                console.error('Error exporting PDF:', error.message);
                this.showError(error.message || 'حدث خطأ في تصدير PDF');
            }
        } finally {
            this.exportBtn.disabled = false;
            this.exportBtn.innerHTML = '<i class="fas fa-download ml-1"></i> تصدير PDF';
        }
    }
    
    showLoading() {
        this.loading.classList.remove('d-none');
        this.reportContent.classList.add('d-none');
        this.hideError();
        this.updateBtn.disabled = true;
    }
    
    hideLoading() {
        this.loading.classList.add('d-none');
        this.updateBtn.disabled = false;
    }
    
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorDisplay.classList.remove('d-none');
        this.hideLoading();
        this.reportContent.classList.add('d-none');
    }
    
    hideError() {
        this.errorDisplay.classList.add('d-none');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PMDailyReport();
});