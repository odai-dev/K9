/**
 * JavaScript for Daily Attendance Sheet Reports
 * Handles frontend interactions for loading and displaying attendance data
 */

class DailyAttendanceReport {
    constructor() {
        this.currentData = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Load report button
        document.getElementById('load-report-btn').addEventListener('click', () => {
            this.loadReport();
        });

        // Export PDF button (in filters)
        document.getElementById('export-pdf-btn').addEventListener('click', () => {
            this.exportPDF();
        });

        // Refresh report button (in report header)
        document.getElementById('refresh-report-btn').addEventListener('click', () => {
            this.loadReport();
        });

        // Download PDF button (in report header)
        document.getElementById('download-pdf-btn').addEventListener('click', () => {
            this.exportPDF();
        });

        // Auto-load if valid params are present
        if (this.hasValidFilters()) {
            this.loadReport();
        }
    }

    hasValidFilters() {
        const projectId = document.getElementById('project-select').value;
        const date = document.getElementById('date-select').value;
        return projectId && date;
    }

    getFilters() {
        return {
            project_id: document.getElementById('project-select').value,
            date: document.getElementById('date-select').value
        };
    }

    showLoading() {
        document.getElementById('loading-indicator').classList.remove('d-none');
    }

    hideLoading() {
        document.getElementById('loading-indicator').classList.add('d-none');
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorAlert = document.getElementById('error-alert');
        
        if (!errorElement || !errorAlert) {
            console.error('Error display elements not found');
            alert(message); // Fallback
            return;
        }
        
        errorElement.textContent = message;
        errorAlert.style.display = 'block';
        errorAlert.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorAlert.classList.remove('show');
            setTimeout(() => {
                errorAlert.style.display = 'none';
            }, 150);
        }, 5000);
    }

    showSuccess(message) {
        const successElement = document.getElementById('success-message');
        const successAlert = document.getElementById('success-alert');
        
        if (!successElement || !successAlert) {
            console.log('Success:', message); // Log success since no UI elements
            return;
        }
        
        successElement.textContent = message;
        successAlert.style.display = 'block';
        successAlert.classList.add('show');
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successAlert.classList.remove('show');
            setTimeout(() => {
                successAlert.style.display = 'none';
            }, 150);
        }, 3000);
    }

    getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!token) {
            console.warn('CSRF token not found in meta tag');
        }
        return token;
    }

    async loadReport() {
        if (!this.hasValidFilters()) {
            this.showError('يرجى اختيار المشروع والتاريخ');
            return;
        }

        const filters = this.getFilters();
        
        try {
            this.showLoading();
            
            const headers = {
                'Content-Type': 'application/json'
            };
            
            const csrfToken = this.getCsrfToken();
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const response = await fetch('/api/reports/attendance/run/daily-sheet', {
                method: 'POST',
                credentials: 'include',
                headers: headers,
                body: JSON.stringify(filters)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'فشل في تحميل التقرير');
            }

            this.currentData = result;
            this.renderReport(result);
            this.showReportArea();

        } catch (error) {
            if (error && error.message) {
                console.error('Error loading report:', error.message);
                this.showError(error.message);
            }
            this.hideReportArea();
        } finally {
            this.hideLoading();
        }
    }

    renderReport(data) {
        // Update report title and subtitle
        const projectSelect = document.getElementById('project-select');
        const projectName = projectSelect.options[projectSelect.selectedIndex]?.text || 'غير محدد';
        
        document.getElementById('report-title').textContent = 'كشف التحضير اليومي';
        document.getElementById('report-subtitle').textContent = `${projectName} - ${data.date}`;

        // Render date information
        this.renderDateInfo(data);

        // Render main tables
        this.renderMainTables(data);

        // Render leave table
        this.renderLeaveTable(data);

        // Show appropriate sections
        const hasData = this.hasReportData(data);
        if (hasData) {
            document.getElementById('date-info-section').style.display = 'block';
            document.getElementById('main-tables-section').style.display = 'block';
            document.getElementById('leave-table-section').style.display = 'block';
            document.getElementById('no-data-message').style.display = 'none';
        } else {
            document.getElementById('date-info-section').style.display = 'none';
            document.getElementById('main-tables-section').style.display = 'none';
            document.getElementById('leave-table-section').style.display = 'none';
            document.getElementById('no-data-message').style.display = 'block';
        }
    }

    hasReportData(data) {
        const groups = data.groups || [];
        const hasGroupData = groups.some(group => group.rows && group.rows.length > 0);
        const hasLeaveData = data.leaves && data.leaves.length > 0;
        return hasGroupData || hasLeaveData;
    }

    renderDateInfo(data) {
        document.getElementById('day-display').textContent = `اليوم: ${data.day_name_ar}`;
        document.getElementById('date-display').textContent = `التاريخ: ${this.formatDateArabic(data.date)}`;
    }

    renderMainTables(data) {
        const groups = data.groups || [];
        
        // Find group 1 and group 2 data
        const group1 = groups.find(g => g.group_no === 1) || { rows: [] };
        const group2 = groups.find(g => g.group_no === 2) || { rows: [] };

        // Render Group 1 table
        this.renderGroup1Table(group1.rows);

        // Render Group 2 table
        this.renderGroup2Table(group2.rows);
    }

    renderGroup1Table(rows) {
        const tbody = document.getElementById('group-1-tbody');
        tbody.innerHTML = '';

        // Ensure minimum 10 rows
        const minRows = 10;
        const totalRows = Math.max(rows.length, minRows);

        for (let i = 0; i < totalRows; i++) {
            const row = rows[i] || {};
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td class="text-center">${row.seq_no || ''}</td>
                <td class="text-center">${this.escapeHtml(row.employee_name || '')}</td>
                <td class="text-center">${this.escapeHtml(row.substitute_name || '')}</td>
                <td class="text-center">${this.escapeHtml(row.dog_name || '')}</td>
                <td class="text-center">${row.check_in_time || ''}</td>
                <td class="text-center signature-cell"></td>
                <td class="text-center">${row.check_out_time || ''}</td>
                <td class="text-center signature-cell"></td>
            `;

            // Add stripe styling
            if (i % 2 === 1) {
                tr.classList.add('table-light');
            }

            tbody.appendChild(tr);
        }
    }

    renderGroup2Table(rows) {
        const tbody = document.getElementById('group-2-tbody');
        tbody.innerHTML = '';

        // Ensure minimum 8 rows
        const minRows = 8;
        const totalRows = Math.max(rows.length, minRows);

        for (let i = 0; i < totalRows; i++) {
            const row = rows[i] || {};
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td class="text-center">${row.seq_no || ''}</td>
                <td class="text-center">${this.escapeHtml(row.employee_or_substitute_name || '')}</td>
                <td class="text-center">${this.escapeHtml(row.dog_name || '')}</td>
                <td class="text-center">${row.check_in_time || ''}</td>
                <td class="text-center signature-cell"></td>
                <td class="text-center">${row.check_out_time || ''}</td>
                <td class="text-center signature-cell"></td>
            `;

            // Add stripe styling
            if (i % 2 === 1) {
                tr.classList.add('table-light');
            }

            tbody.appendChild(tr);
        }
    }

    renderLeaveTable(data) {
        const tbody = document.getElementById('leave-tbody');
        tbody.innerHTML = '';

        const leaves = data.leaves || [];
        
        // Ensure minimum 3 rows
        const minRows = 3;
        const totalRows = Math.max(leaves.length, minRows);

        for (let i = 0; i < totalRows; i++) {
            const leave = leaves[i] || {};
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td class="text-center">${leave.seq_no || ''}</td>
                <td class="text-center">${this.escapeHtml(leave.employee_name || '')}</td>
                <td class="text-center">${this.escapeHtml(leave.leave_type || '')}</td>
                <td class="text-center">${this.escapeHtml(leave.note || '')}</td>
            `;

            // Add stripe styling
            if (i % 2 === 1) {
                tr.classList.add('table-warning');
            }

            tbody.appendChild(tr);
        }
    }

    async exportPDF() {
        if (!this.hasValidFilters()) {
            this.showError('يرجى اختيار المشروع والتاريخ أولاً');
            return;
        }

        const filters = this.getFilters();
        
        try {
            this.showLoading();
            
            const headers = {
                'Content-Type': 'application/json'
            };
            
            const csrfToken = this.getCsrfToken();
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const response = await fetch('/api/reports/attendance/export/pdf/daily-sheet', {
                method: 'POST',
                credentials: 'include',
                headers: headers,
                body: JSON.stringify(filters)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error:', errorText);
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            console.log('PDF export result:', result);

            // Trigger download
            if (result && result.path) {
                this.downloadFile(result.path);
                this.showSuccess('تم تصدير التقرير بنجاح');
            } else {
                throw new Error('No file path returned from server');
            }

        } catch (error) {
            if (error && error.message) {
                console.error('Error exporting PDF:', error.message);
                this.showError(error.message);
            }
        } finally {
            this.hideLoading();
        }
    }

    downloadFile(filePath) {
        try {
            console.log('Attempting to download file:', filePath);
            
            // Create a temporary download link
            const link = document.createElement('a');
            const fullPath = filePath.startsWith('/') ? filePath : '/' + filePath;
            const fileName = filePath.split('/').pop();
            
            console.log('Full path:', fullPath);
            console.log('File name:', fileName);
            
            link.href = fullPath;
            link.download = fileName;
            link.target = '_blank';
            link.style.display = 'none';
            
            document.body.appendChild(link);
            
            // Alternative approach: Try both click events
            if (link.click) {
                link.click();
            } else {
                // Fallback for older browsers
                const event = new MouseEvent('click');
                link.dispatchEvent(event);
            }
            
            // Clean up
            setTimeout(() => {
                if (document.body.contains(link)) {
                    document.body.removeChild(link);
                }
            }, 100);
            
            console.log('Download triggered successfully');
            
        } catch (error) {
            console.error('Error in downloadFile:', error);
            // Fallback: open in new window
            try {
                const fullPath = filePath.startsWith('/') ? filePath : '/' + filePath;
                window.open(fullPath, '_blank');
            } catch (fallbackError) {
                console.error('Fallback download also failed:', fallbackError);
                this.showError('فشل في تحميل الملف. يرجى المحاولة مرة أخرى.');
            }
        }
    }

    showReportArea() {
        document.getElementById('report-content-area').style.display = 'block';
    }

    hideReportArea() {
        document.getElementById('report-content-area').style.display = 'none';
    }

    formatDateArabic(dateStr) {
        // Convert date to DD/MM/YYYY format with standard numerals
        // Split the string to avoid timezone issues with Date constructor
        const [year, month, day] = dateStr.split('-');
        
        return `${day}/${month}/${year}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new DailyAttendanceReport();
});

// Add CSS for signature cells
const style = document.createElement('style');
style.textContent = `
    .signature-cell {
        height: 30px;
        background-color: #f8f9fa;
        border: 1px dashed #dee2e6 !important;
    }
    
    .signature-cell::after {
        content: "";
        display: block;
        width: 100%;
        height: 1px;
        background-color: #dee2e6;
        margin-top: 20px;
    }
`;
document.head.appendChild(style);