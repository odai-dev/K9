/*
 * Caretaker Daily Reports JavaScript
 * Handles Arabic/RTL caretaker daily reports with unified filters and PDF export
 */

// Global state
let currentData = null;
let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Button handlers
    document.getElementById('load-report-btn').addEventListener('click', loadReport);
    document.getElementById('export-pdf-btn').addEventListener('click', exportPDF);
    document.getElementById('prev-page-btn').addEventListener('click', () => loadReport(currentPage - 1));
    document.getElementById('next-page-btn').addEventListener('click', () => loadReport(currentPage + 1));
});

function loadReport(page = 1) {
    const formData = getFormData();
    if (!formData) return;
    
    currentPage = page;
    showLoading();
    
    // Build API URL
    const params = new URLSearchParams({
        range_type: formData.range_type,
        page: page,
        per_page: 50
    });
    
    if (formData.project_id) params.set('project_id', formData.project_id);
    if (formData.dog_id) params.set('dog_id', formData.dog_id);
    if (formData.date) params.set('date', formData.date);
    if (formData.week_start) params.set('week_start', formData.week_start);
    if (formData.year_month) params.set('year_month', formData.year_month);
    if (formData.date_from) params.set('date_from', formData.date_from);
    if (formData.date_to) params.set('date_to', formData.date_to);
    
    fetch(`/api/reports/breeding/caretaker-daily/unified?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                return;
            }
            
            currentData = data;
            totalPages = data.pagination.pages;
            
            updateKPIs(data.kpis);
            updateTable(data.rows);
            updatePagination(data.pagination);
            
            document.getElementById('report-content-area').style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading report:', error);
            showError('حدث خطأ أثناء تحميل التقرير');
        })
        .finally(() => {
            hideLoading();
        });
}

function exportPDF() {
    const formData = getFormData();
    if (!formData) return;
    
    // Update form fields for export
    const form = document.getElementById('pdf-export-form');
    document.getElementById('export-range-type').value = formData.range_type || '';
    document.getElementById('export-project-id').value = formData.project_id || '';
    document.getElementById('export-dog-id').value = formData.dog_id || '';
    document.getElementById('export-date').value = formData.date || '';
    document.getElementById('export-week-start').value = formData.week_start || '';
    document.getElementById('export-year-month').value = formData.year_month || '';
    document.getElementById('export-date-from').value = formData.date_from || '';
    document.getElementById('export-date-to').value = formData.date_to || '';
    
    form.action = '/api/reports/breeding/caretaker-daily/unified/export.pdf';
    form.submit();
}

function updateKPIs(kpis) {
    // Update main KPIs
    document.getElementById('total-entries').textContent = kpis.total_entries || 0;
    document.getElementById('unique-dogs').textContent = kpis.unique_dogs || 0;
    
    // Update house cleaning KPIs
    if (kpis.house_tasks) {
        document.getElementById('house-clean-count').textContent = kpis.house_tasks.house_clean || 0;
        document.getElementById('house-clean-pct').textContent = (kpis.house_tasks.house_clean_pct || 0) + '%';
    }
    
    // Update dog cleaning KPIs
    if (kpis.dog_tasks) {
        document.getElementById('dog-clean-count').textContent = kpis.dog_tasks.dog_clean || 0;
        document.getElementById('dog-clean-pct').textContent = (kpis.dog_tasks.dog_clean_pct || 0) + '%';
        
        // Full cleaning stats (both house and dog)
        const fullCleanCount = Math.min(kpis.house_tasks?.full_house_clean || 0, kpis.dog_tasks?.full_dog_grooming || 0);
        const fullCleanPct = kpis.total_entries > 0 ? Math.round((fullCleanCount / kpis.total_entries) * 100) : 0;
        document.getElementById('full-clean-count').textContent = fullCleanCount;
        document.getElementById('full-clean-pct').textContent = fullCleanPct + '%';
    }
    
    // Update date range display
    if (currentData && currentData.range_display) {
        document.getElementById('date-range-display').textContent = currentData.range_display;
    }
}

function updateTable(rows) {
    const tbody = document.querySelector('#caretaker-daily-table tbody');
    tbody.innerHTML = '';
    
    if (!rows || rows.length === 0) {
        showEmptyState();
        return;
    }
    
    hideEmptyState();
    
    rows.forEach(row => {
        const tr = document.createElement('tr');
        // RTL-ordered columns matching the 2-row header structure
        tr.innerHTML = `
            <td class="text-center">${row.التاريخ || ''}</td>
            <td class="text-center">${row.اسم_الكلب || ''}</td>
            <td class="text-center">${row.رمز_الكلب || ''}</td>
            <td class="text-center">${row.رقم_البيت || ''}</td>
            <td class="text-center">${row.القائم_بالرعاية || ''}</td>
            <!-- Dog Grooming columns (reversed order for RTL) -->
            <td class="text-center">${getBadgeHtml(row.تنظيف_الأواني)}</td>
            <td class="text-center">${getBadgeHtml(row.تمشيط_الكلب)}</td>
            <td class="text-center">${getBadgeHtml(row.استحمام_الكلب)}</td>
            <td class="text-center">${getBadgeHtml(row.تنظيف_الكلب)}</td>
            <!-- House Cleaning columns (reversed order for RTL) -->
            <td class="text-center">${getBadgeHtml(row.تنظيف_البالوعة)}</td>
            <td class="text-center">${getBadgeHtml(row.تنظيف_الصنبور)}</td>
            <td class="text-center">${getBadgeHtml(row.شفط_البيت)}</td>
            <td class="text-center">${getBadgeHtml(row.تنظيف_البيت)}</td>
            <!-- Additional Info -->
            <td class="text-start" style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${row.ملاحظات || ''}">${row.ملاحظات || '-'}</td>
            <td class="text-center small">${row.وقت_التسجيل || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

function getBadgeHtml(value) {
    const isCompleted = value === 'نعم';
    const badgeClass = isCompleted ? 'bg-success' : 'bg-secondary';
    const icon = isCompleted ? '<i class="fas fa-check me-1"></i>' : '<i class="fas fa-times me-1"></i>';
    return `<span class="badge ${badgeClass}">${icon}${value || 'لا'}</span>`;
}

function updatePagination(pagination) {
    document.getElementById('page-info').textContent = `صفحة ${pagination.page} من ${pagination.pages}`;
    document.getElementById('prev-page-btn').disabled = !pagination.has_prev;
    document.getElementById('next-page-btn').disabled = !pagination.has_next;
}

function showLoading() {
    document.getElementById('table-loading').classList.remove('d-none');
    hideEmptyState();
}

function hideLoading() {
    document.getElementById('table-loading').classList.add('d-none');
}

function showEmptyState() {
    document.getElementById('empty-state').classList.remove('d-none');
    hideLoading();
}

function hideEmptyState() {
    document.getElementById('empty-state').classList.add('d-none');
}

function showError(message) {
    // Create a toast or use alert for error display
    if (typeof showToast === 'function') {
        showToast(message, 'error');
    } else {
        alert(message);
    }
    hideLoading();
    showEmptyState();
}

// Helper function to get form data from unified filters
function getFormData() {
    // Get form data using correct DOM IDs from unified filters
    const rangeType = document.getElementById('range-type')?.value || 'daily';
    const projectId = document.getElementById('project-select')?.value || '';
    const dogId = document.getElementById('dog-select')?.value || '';
    
    // Validate required fields based on range type
    if (!rangeType) {
        showError('يرجى تحديد نوع النطاق الزمني');
        return null;
    }
    
    const formData = { 
        range_type: rangeType, 
        project_id: projectId, 
        dog_id: dogId 
    };
    
    // Add range-specific parameters with validation using correct IDs
    if (rangeType === 'daily') {
        const date = document.getElementById('date-select')?.value || '';
        if (!date) {
            showError('يرجى تحديد التاريخ');
            return null;
        }
        formData.date = date;
    } else if (rangeType === 'weekly') {
        const weekStart = document.getElementById('week-start-select')?.value || '';
        if (!weekStart) {
            showError('يرجى تحديد بداية الأسبوع');
            return null;
        }
        formData.week_start = weekStart;
    } else if (rangeType === 'monthly') {
        const yearMonth = document.getElementById('year-month-select')?.value || '';
        if (!yearMonth) {
            showError('يرجى تحديد الشهر والسنة');
            return null;
        }
        formData.year_month = yearMonth;
    } else if (rangeType === 'custom') {
        const dateFrom = document.getElementById('date-from-select')?.value || '';
        const dateTo = document.getElementById('date-to-select')?.value || '';
        if (!dateFrom || !dateTo) {
            showError('يرجى تحديد تاريخ البداية والنهاية');
            return null;
        }
        formData.date_from = dateFrom;
        formData.date_to = dateTo;
    }
    
    return formData;
}