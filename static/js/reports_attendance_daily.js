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
        document.getElementById('error-message').textContent = message;
        const errorAlert = document.getElementById('error-alert');
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
        document.getElementById('success-message').textContent = message;
        const successAlert = document.getElementById('success-alert');
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

    async loadReport() {
        if (!this.hasValidFilters()) {
            this.showError('يرجى اختيار المشروع والتاريخ');
            return;
        }

        const filters = this.getFilters();
        
        try {
            this.showLoading();
            
            const response = await fetch('/api/reports/attendance/run/daily-sheet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
            console.error('Error loading report:', error);
            this.showError(error.message);
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
            
            const response = await fetch('/api/reports/attendance/export/pdf/daily-sheet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'فشل في تصدير PDF');
            }

            // Trigger download
            this.downloadFile(result.path);
            this.showSuccess('تم تصدير التقرير بنجاح');

        } catch (error) {
            console.error('Error exporting PDF:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    downloadFile(filePath) {
        // Create a temporary download link
        const link = document.createElement('a');
        link.href = filePath.startsWith('/') ? filePath : '/' + filePath; // Ensure absolute path
        link.download = filePath.split('/').pop(); // Get filename
        link.target = '_blank'; // Open in new tab for better browser support
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    showReportArea() {
        document.getElementById('report-content-area').style.display = 'block';
    }

    hideReportArea() {
        document.getElementById('report-content-area').style.display = 'none';
    }

    formatDateArabic(dateStr) {
        // Convert date to Arabic format (dd/mm/yyyy with Arabic numerals)
        const date = new Date(dateStr);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        const englishDate = `${day}/${month}/${year}`;
        
        // Convert to Arabic numerals
        const arabicNumerals = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
        };
        
        return englishDate.replace(/[0-9]/g, (digit) => arabicNumerals[digit] || digit);
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