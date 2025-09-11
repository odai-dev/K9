/**
 * Daily & Weekly Checkup Reports JavaScript
 * Handles Arabic RTL checkup reports with reversed column tables
 */

let currentReportType = 'daily';
let currentPage = 1;
let totalPages = 1;

// Arabic day names for display
const ARABIC_DAYS = {
    'Mon': 'الاثنين',
    'Tue': 'الثلاثاء', 
    'Wed': 'الأربعاء',
    'Thu': 'الخميس',
    'Fri': 'الجمعة',
    'Sat': 'السبت',
    'Sun': 'الأحد'
};

// Severity levels for display
const SEVERITY_LABELS = {
    'خفيف': 'خفيف',
    'متوسط': 'متوسط', 
    'شديد': 'شديد'
};

// Body part Arabic names
const BODY_PARTS = {
    'العين': 'العين',
    'الأذن': 'الأذن',
    'الأنف': 'الأنف',
    'الأطراف الأمامية': 'الأطراف الأمامية',
    'الأطراف الخلفية': 'الأطراف الخلفية',
    'الشعر': 'الشعر',
    'الذيل': 'الذيل'
};

/**
 * Initialize checkup report functionality
 * @param {string} reportType - 'daily' or 'weekly'
 */
function initializeCheckupReport(reportType) {
    currentReportType = reportType;
    
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    if (reportType === 'daily') {
        document.getElementById('date-select').value = today;
    } else {
        // For weekly, set to Monday of current week
        const date = new Date();
        const day = date.getDay();
        const diff = date.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
        const monday = new Date(date.setDate(diff));
        document.getElementById('week-start-select').value = monday.toISOString().split('T')[0];
    }
    
    setupEventListeners();
    updateButtonStates();
    loadDogsForProject(''); // Load all dogs initially
}

/**
 * Set up event listeners for form elements
 */
function setupEventListeners() {
    const projectSelect = document.getElementById('project-select');
    const dateSelect = document.getElementById('date-select');
    const weekStartSelect = document.getElementById('week-start-select');
    const loadBtn = document.getElementById('load-report-btn');
    const exportBtn = document.getElementById('export-pdf-btn');
    
    // Project change handler
    projectSelect.addEventListener('change', function() {
        updateButtonStates();
        loadDogsForProject(this.value);
    });
    
    // Date/Week change handlers
    if (dateSelect) {
        dateSelect.addEventListener('change', updateButtonStates);
    }
    if (weekStartSelect) {
        weekStartSelect.addEventListener('change', updateButtonStates);
    }
    
    // Button click handlers
    loadBtn.addEventListener('click', loadReport);
    exportBtn.addEventListener('click', exportToPDF);
}

/**
 * Update button states based on form validity
 */
function updateButtonStates() {
    const dateSelect = document.getElementById('date-select');
    const weekStartSelect = document.getElementById('week-start-select');
    const loadBtn = document.getElementById('load-report-btn');
    const exportBtn = document.getElementById('export-pdf-btn');
    
    let hasRequiredDate = false;
    
    if (currentReportType === 'daily' && dateSelect) {
        hasRequiredDate = dateSelect.value.trim() !== '';
    } else if (currentReportType === 'weekly' && weekStartSelect) {
        hasRequiredDate = weekStartSelect.value.trim() !== '';
    }
    
    loadBtn.disabled = !hasRequiredDate;
    exportBtn.disabled = !hasRequiredDate;
}

/**
 * Load dogs for selected project
 * @param {string} projectId - Project ID or empty string for all projects
 */
function loadDogsForProject(projectId) {
    const dogSelect = document.getElementById('dog-select');
    
    // Clear and show loading
    dogSelect.innerHTML = '<option value="">جاري التحميل...</option>';
    
    // Build API URL
    let apiUrl = '/api/dogs?status=ACTIVE&limit=100';
    if (projectId) {
        apiUrl += `&project_id=${projectId}`;
    }
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            dogSelect.innerHTML = '<option value="">جميع الكلاب</option>';
            if (data.success && data.data) {
                data.data.forEach(dog => {
                    const option = document.createElement('option');
                    option.value = dog.id;
                    option.textContent = `${dog.name} (${dog.code || dog.id.substring(0,8)})`;
                    dogSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading dogs:', error);
            dogSelect.innerHTML = '<option value="">جميع الكلاب</option>';
        });
}

/**
 * Load checkup report data
 */
async function loadReport() {
    const loadingIndicator = document.getElementById('loading-indicator');
    const reportContentArea = document.getElementById('report-content-area');
    
    try {
        // Show loading
        loadingIndicator.classList.remove('d-none');
        reportContentArea.style.display = 'none';
        
        // Get form data
        const formData = getFormData();
        if (!formData) return;
        
        // Build API URL
        const apiUrl = buildApiUrl(formData);
        
        // Fetch data
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'خطأ في تحميل البيانات');
        }
        
        // Display data
        if (currentReportType === 'daily') {
            displayDailyReport(data);
        } else {
            displayWeeklyReport(data);
        }
        
        // Show report content
        reportContentArea.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading report:', error);
        showError('خطأ في تحميل التقرير: ' + error.message);
    } finally {
        // Hide loading
        loadingIndicator.classList.add('d-none');
    }
}

/**
 * Get form data for API request
 * @returns {Object|null} Form data object or null if invalid
 */
function getFormData() {
    const projectSelect = document.getElementById('project-select');
    const dateSelect = document.getElementById('date-select');
    const weekStartSelect = document.getElementById('week-start-select');
    const dogSelect = document.getElementById('dog-select');
    
    const data = {
        project_id: projectSelect.value || '',
        dog_id: dogSelect.value || ''
    };
    
    if (currentReportType === 'daily') {
        if (!dateSelect.value) {
            showError('يرجى اختيار التاريخ');
            return null;
        }
        data.date = dateSelect.value;
    } else {
        if (!weekStartSelect.value) {
            showError('يرجى اختيار بداية الأسبوع');
            return null;
        }
        data.week_start = weekStartSelect.value;
    }
    
    return data;
}

/**
 * Build API URL from form data
 * @param {Object} formData - Form data object
 * @returns {string} API URL
 */
function buildApiUrl(formData) {
    const baseUrl = `/api/reports/breeding/checkup/${currentReportType}`;
    const params = new URLSearchParams();
    
    Object.keys(formData).forEach(key => {
        if (formData[key]) {
            params.append(key, formData[key]);
        }
    });
    
    // Add pagination
    params.append('page', currentPage.toString());
    params.append('per_page', '50');
    
    return `${baseUrl}?${params.toString()}`;
}

/**
 * Display daily report data
 * @param {Object} data - Report data from API
 */
function displayDailyReport(data) {
    // Update KPIs
    updateDailyKPIs(data.kpis);
    
    // Update pagination info
    updatePaginationInfo(data.pagination);
    
    // Display table with REVERSED columns (RIGHT→LEFT as specified)
    displayDailyTable(data.rows);
    
    // Update pagination controls
    updatePaginationControls(data.pagination);
}

/**
 * Display weekly report data
 * @param {Object} data - Report data from API
 */
function displayWeeklyReport(data) {
    // Update KPIs
    updateWeeklyKPIs(data.kpis);
    
    // Update pagination info
    updatePaginationInfo(data.pagination);
    
    // Display table with REVERSED columns (RIGHT→LEFT as specified)
    displayWeeklyTable(data.table);
    
    // Update pagination controls
    updatePaginationControls(data.pagination);
}

/**
 * Update daily KPIs display
 * @param {Object} kpis - KPI data
 */
function updateDailyKPIs(kpis) {
    document.getElementById('total-checks').textContent = kpis.total_checks || 0;
    document.getElementById('unique-dogs').textContent = kpis.unique_dogs || 0;
    document.getElementById('moderate-cases').textContent = kpis.by_severity?.['متوسط'] || 0;
    document.getElementById('severe-cases').textContent = kpis.by_severity?.['شديد'] || 0;
    
    // Display top flagged body parts
    const topFlagsContainer = document.getElementById('top-flags-container');
    if (kpis.flags && Object.keys(kpis.flags).length > 0) {
        const sortedFlags = Object.entries(kpis.flags)
            .filter(([_, count]) => count > 0)
            .sort(([_, a], [__, b]) => b - a)
            .slice(0, 3);
        
        topFlagsContainer.innerHTML = sortedFlags.map(([part, count]) => 
            `<span class="badge bg-warning me-2">${part}: ${count}</span>`
        ).join('');
    } else {
        topFlagsContainer.innerHTML = '<span class="text-muted">لا توجد ملاحظات</span>';
    }
}

/**
 * Update weekly KPIs display
 * @param {Object} kpis - KPI data
 */
function updateWeeklyKPIs(kpis) {
    document.getElementById('dogs-count').textContent = kpis.dogs_count || 0;
    document.getElementById('checks-count').textContent = kpis.checks_count || 0;
    document.getElementById('flagged-dogs').textContent = kpis.flagged_dogs || 0;
    
    const avgChecks = kpis.dogs_count > 0 ? Math.round(kpis.checks_count / kpis.dogs_count * 10) / 10 : 0;
    document.getElementById('avg-checks-per-dog').textContent = avgChecks;
    
    // Display severity distribution
    const severityContainer = document.getElementById('severity-distribution-container');
    if (kpis.by_severity && Object.keys(kpis.by_severity).length > 0) {
        severityContainer.innerHTML = Object.entries(kpis.by_severity)
            .map(([severity, count]) => {
                const color = severity === 'شديد' ? 'danger' : severity === 'متوسط' ? 'warning' : 'success';
                return `<div class="text-center">
                    <div class="badge bg-${color} fs-6">${count}</div>
                    <div class="small text-muted">${severity}</div>
                </div>`;
            }).join('');
    } else {
        severityContainer.innerHTML = '<span class="text-muted">لا توجد بيانات</span>';
    }
}

/**
 * Display daily table with REVERSED columns (RIGHT→LEFT order)
 * @param {Array} rows - Table row data
 */
function displayDailyTable(rows) {
    const tableContainer = document.getElementById('checkup-table-container');
    
    if (!rows || rows.length === 0) {
        tableContainer.innerHTML = '<div class="text-center text-muted py-4">لا توجد بيانات للعرض</div>';
        return;
    }
    
    // Define headers in RIGHT→LEFT order as specified
    const headers = [
        "التاريخ", "الوقت",
        "العين", "الأذن", "الأنف", "الأطراف الأمامية", "الأطراف الخلفية", "الشعر", "الذيل",
        "شدة الحالة", "ملاحظات",
        "المربي", "الكلب", "المشروع"
    ];
    
    let tableHTML = `
        <table class="table table-hover table-bordered">
            <thead class="table-dark">
                <tr>
                    ${headers.map(header => `<th class="text-center">${header}</th>`).join('')}
                </tr>
            </thead>
            <tbody>`;
    
    rows.forEach(row => {
        // Map row data to match the header order (RIGHT→LEFT)
        const cellData = [
            row.date,
            row.time,
            formatBodyPartStatus(row['العين']),
            formatBodyPartStatus(row['الأذن']),
            formatBodyPartStatus(row['الأنف']),
            formatBodyPartStatus(row['الأطراف الأمامية']),
            formatBodyPartStatus(row['الأطراف الخلفية']),
            formatBodyPartStatus(row['الشعر']),
            formatBodyPartStatus(row['الذيل']),
            formatSeverity(row['شدة الحالة']),
            truncateText(row['ملاحظات'], 50),
            row['المربي'],
            row.dog_name,
            row.project_name || 'غير محدد'
        ];
        
        tableHTML += `<tr>${cellData.map(cell => `<td class="text-center">${cell || '-'}</td>`).join('')}</tr>`;
    });
    
    tableHTML += '</tbody></table>';
    tableContainer.innerHTML = tableHTML;
}

/**
 * Display weekly table with REVERSED columns (RIGHT→LEFT order)
 * @param {Array} tableData - Weekly table data
 */
function displayWeeklyTable(tableData) {
    const tableContainer = document.getElementById('checkup-table-container');
    
    if (!tableData || tableData.length === 0) {
        tableContainer.innerHTML = '<div class="text-center text-muted py-4">لا توجد بيانات للعرض</div>';
        return;
    }
    
    // Define headers in RIGHT→LEFT order as specified
    const headers = [
        "مجموع الملاحظات", "أقصى شدة خلال الأسبوع",
        "الأحد", "السبت", "الجمعة", "الخميس", "الأربعاء", "الثلاثاء", "الاثنين",
        "العين", "الأذن", "الأنف", "الأطراف الأمامية", "الأطراف الخلفية", "الشعر", "الذيل",
        "عدد الفحوصات", "الكلب", "الكود"
    ];
    
    let tableHTML = `
        <table class="table table-hover table-bordered">
            <thead class="table-dark">
                <tr>
                    ${headers.map(header => `<th class="text-center">${header}</th>`).join('')}
                </tr>
            </thead>
            <tbody>`;
    
    tableData.forEach(dogData => {
        // Map dog data to match the header order (RIGHT→LEFT)
        const cellData = [
            dogData.flags_total,
            formatSeverity(dogData.severity_max),
            formatDayCell(dogData.days['Sun']),
            formatDayCell(dogData.days['Sat']),
            formatDayCell(dogData.days['Fri']),
            formatDayCell(dogData.days['Thu']),
            formatDayCell(dogData.days['Wed']),
            formatDayCell(dogData.days['Tue']),
            formatDayCell(dogData.days['Mon']),
            dogData.flags_by_part['العين'] || 0,
            dogData.flags_by_part['الأذن'] || 0,
            dogData.flags_by_part['الأنف'] || 0,
            dogData.flags_by_part['الأطراف الأمامية'] || 0,
            dogData.flags_by_part['الأطراف الخلفية'] || 0,
            dogData.flags_by_part['الشعر'] || 0,
            dogData.flags_by_part['الذيل'] || 0,
            dogData.checks,
            dogData.dog_name,
            dogData.dog_code
        ];
        
        tableHTML += `<tr>${cellData.map(cell => `<td class="text-center">${cell || '-'}</td>`).join('')}</tr>`;
    });
    
    tableHTML += '</tbody></table>';
    tableContainer.innerHTML = tableHTML;
}

/**
 * Format body part status for display
 * @param {string} status - Body part status
 * @returns {string} Formatted status
 */
function formatBodyPartStatus(status) {
    if (!status) return '-';
    
    // Highlight abnormal findings
    const normalValues = ['طبيعي', 'سليم'];
    if (normalValues.includes(status)) {
        return `<span class="badge bg-success">${status}</span>`;
    } else {
        return `<span class="badge bg-warning">${status}</span>`;
    }
}

/**
 * Format severity level for display
 * @param {string} severity - Severity level
 * @returns {string} Formatted severity
 */
function formatSeverity(severity) {
    if (!severity) return '-';
    
    const colors = {
        'خفيف': 'success',
        'متوسط': 'warning',
        'شديد': 'danger'
    };
    
    const color = colors[severity] || 'secondary';
    return `<span class="badge bg-${color}">${severity}</span>`;
}

/**
 * Format day cell for weekly table
 * @param {Object} dayData - Day data object
 * @returns {string} Formatted day cell
 */
function formatDayCell(dayData) {
    if (!dayData || (!dayData.severity && !dayData.flags)) {
        return '-';
    }
    
    let content = '';
    if (dayData.severity) {
        const severityLetter = dayData.severity === 'شديد' ? 'ش' : dayData.severity === 'متوسط' ? 'م' : 'خ';
        content += `<span class="badge bg-info me-1">${severityLetter}</span>`;
    }
    if (dayData.flags > 0) {
        content += `<small class="text-danger">${dayData.flags}</small>`;
    }
    
    return content || '-';
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
    if (!text) return '-';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

/**
 * Update pagination info display
 * @param {Object} pagination - Pagination data
 */
function updatePaginationInfo(pagination) {
    const paginationInfo = document.getElementById('pagination-info');
    if (pagination && pagination.total > 0) {
        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total);
        paginationInfo.textContent = `عرض ${start}-${end} من ${pagination.total} عنصر`;
    } else {
        paginationInfo.textContent = '';
    }
}

/**
 * Update pagination controls
 * @param {Object} pagination - Pagination data
 */
function updatePaginationControls(pagination) {
    const paginationNav = document.getElementById('pagination-nav');
    
    if (!pagination || pagination.pages <= 1) {
        paginationNav.innerHTML = '';
        return;
    }
    
    currentPage = pagination.page;
    totalPages = pagination.pages;
    
    let paginationHTML = '<ul class="pagination justify-content-center mb-0">';
    
    // Previous button
    if (pagination.has_prev) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${pagination.page - 1})">السابق</a>
            </li>`;
    }
    
    // Page numbers (show max 5 pages around current page)
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === pagination.page ? 'active' : '';
        paginationHTML += `
            <li class="page-item ${activeClass}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>`;
    }
    
    // Next button
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${pagination.page + 1})">التالي</a>
            </li>`;
    }
    
    paginationHTML += '</ul>';
    paginationNav.innerHTML = paginationHTML;
}

/**
 * Change to a specific page
 * @param {number} page - Page number
 */
function changePage(page) {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
        currentPage = page;
        loadReport();
    }
}

/**
 * Export report to PDF
 */
async function exportToPDF() {
    const exportBtn = document.getElementById('export-pdf-btn');
    const originalText = exportBtn.innerHTML;
    
    try {
        // Show loading
        exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التصدير...';
        exportBtn.disabled = true;
        
        // Get form data
        const formData = getFormData();
        if (!formData) return;
        
        // Build export URL
        const baseUrl = `/api/reports/breeding/checkup/${currentReportType}/export.pdf`;
        const params = new URLSearchParams(formData);
        const exportUrl = `${baseUrl}?${params.toString()}`;
        
        // Make export request
        const response = await fetch(exportUrl);
        const result = await response.json();
        
        if (result.success) {
            // Create download link
            const link = document.createElement('a');
            link.href = '/' + result.file;
            link.download = result.filename;
            link.click();
            
            showSuccess('تم تصدير الملف بنجاح');
        } else {
            throw new Error(result.error || 'خطأ في تصدير الملف');
        }
        
    } catch (error) {
        console.error('Export error:', error);
        showError('خطأ في تصدير الملف: ' + error.message);
    } finally {
        // Reset button
        exportBtn.innerHTML = originalText;
        exportBtn.disabled = false;
    }
}

/**
 * Show success message
 * @param {string} message - Success message
 */
function showSuccess(message) {
    // Create and show toast/alert (simplified version)
    console.log('Success:', message);
    alert(message); // In production, use a proper toast notification
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    // Create and show toast/alert (simplified version)
    console.error('Error:', message);
    alert(message); // In production, use a proper toast notification
}