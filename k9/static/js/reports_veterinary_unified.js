/**
 * Unified Veterinary Reports JavaScript
 * Handles Arabic RTL interface, date range filters, and dynamic table rendering
 */

document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const rangeTypeSelect = document.getElementById('range_type');
    const dogSelect = document.getElementById('dog_id');
    const showKpisCheck = document.getElementById('show_kpis');
    const exportBtn = document.getElementById('export-pdf');
    
    // Elements for showing/hiding content
    const reportContentArea = document.getElementById('report-content-area');
    const loadingIndicator = document.getElementById('loading-indicator');
    const noDataMessage = document.getElementById('no-data-message');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    // Date input containers
    const dailyDate = document.getElementById('daily-date');
    const weeklyStart = document.getElementById('weekly-start');
    const monthlyInput = document.getElementById('monthly-input');
    const customFrom = document.getElementById('custom-from');
    const customTo = document.getElementById('custom-to');
    
    // KPI elements
    const kpiCards = document.getElementById('kpi-cards');
    const totalVisits = document.getElementById('total-visits');
    const routineVisits = document.getElementById('routine-visits');
    const emergencyVisits = document.getElementById('emergency-visits');
    const vaccinationVisits = document.getElementById('vaccination-visits');
    const totalMedications = document.getElementById('total-medications');
    const totalCost = document.getElementById('total-cost');
    
    // Table elements
    const tableHeaders = document.getElementById('table-headers');
    const tableBody = document.getElementById('table-body');
    
    // Get CSRF token
    const csrfToken = document.getElementById('csrf_token').value;
    
    /**
     * Show/hide date inputs based on range type
     */
    function toggleDateInputs() {
        const rangeType = rangeTypeSelect.value;
        
        // Hide all date inputs first
        [dailyDate, weeklyStart, monthlyInput, customFrom, customTo].forEach(el => {
            el.style.display = 'none';
        });
        
        // Show relevant inputs
        switch(rangeType) {
            case 'daily':
                dailyDate.style.display = 'block';
                break;
            case 'weekly':
                weeklyStart.style.display = 'block';
                break;
            case 'monthly':
                monthlyInput.style.display = 'block';
                break;
            case 'custom':
                customFrom.style.display = 'block';
                customTo.style.display = 'block';
                break;
        }
    }
    
    /**
     * Load available dogs for the dog filter
     */
    async function loadDogs() {
        try {
            const projectId = document.getElementById('project_id').value;
            let url = '/api/dogs';
            const params = new URLSearchParams();
            params.append('status', 'ACTIVE');
            params.append('limit', '50');
            if (projectId) {
                params.append('project_id', projectId);
            }
            url += `?${params.toString()}`;
            
            const response = await fetch(url, {
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (response.ok) {
                const apiResponse = await response.json();
                const dogs = apiResponse.data || [];
                
                // Clear existing options except "all dogs"
                dogSelect.innerHTML = '<option value="">جميع الكلاب</option>';
                
                // Add dog options
                dogs.forEach(dog => {
                    const option = document.createElement('option');
                    option.value = dog.id;
                    option.textContent = `${dog.name} (${dog.code || dog.microchip_id})`;
                    dogSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading dogs:', error);
        }
    }
    
    /**
     * Show loading state
     */
    function showLoading() {
        reportContentArea.style.display = 'none';
        noDataMessage.style.display = 'none';
        errorMessage.style.display = 'none';
        loadingIndicator.style.display = 'block';
    }
    
    /**
     * Hide loading state
     */
    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        hideLoading();
        errorText.textContent = message;
        errorMessage.style.display = 'block';
        reportContentArea.style.display = 'none';
        noDataMessage.style.display = 'none';
    }
    
    /**
     * Show no data message
     */
    function showNoData() {
        hideLoading();
        noDataMessage.style.display = 'block';
        reportContentArea.style.display = 'none';
        errorMessage.style.display = 'none';
    }
    
    /**
     * Update KPI cards
     */
    function updateKPIs(kpis) {
        if (!kpis) {
            kpiCards.style.display = 'none';
            return;
        }
        
        kpiCards.style.display = 'block';
        
        totalVisits.textContent = kpis.total_visits || 0;
        routineVisits.textContent = kpis.by_visit_type['روتيني'] || 0;
        emergencyVisits.textContent = kpis.by_visit_type['طارئ'] || 0;
        vaccinationVisits.textContent = kpis.by_visit_type['تطعيم'] || 0;
        totalMedications.textContent = kpis.total_medications || 0;
        totalCost.textContent = kpis.total_cost || 0;
    }
    
    /**
     * Format medications for display
     */
    function formatMedications(medications) {
        if (!medications || medications.length === 0) {
            return '';
        }
        
        return medications.map(med => {
            if (med.name && med.dose) {
                return `${med.name} (${med.dose})`;
            }
            return med.name || '';
        }).join(', ');
    }
    
    /**
     * Render daily table (detailed rows) - RTL column order
     */
    function renderDailyTable(rows) {
        // Arabic headers in RTL order (right to left)
        const headers = [
            'المشروع', 'الكلب', 'اسم الطبيب', 'ملاحظات', 'المدة (دقيقة)', 
            'التكلفة', 'الأدوية', 'العلاج', 'التشخيص', 'نوع الزيارة', 'الوقت', 'التاريخ'
        ];
        
        // Create header row
        tableHeaders.innerHTML = '';
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            th.className = 'text-center';
            headerRow.appendChild(th);
        });
        tableHeaders.appendChild(headerRow);
        
        // Create data rows in RTL order
        tableBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            
            // Data in RTL order to match headers
            const cellData = [
                row.project_name,
                row.dog_name,
                row.vet_name,
                row.notes,
                row.duration_min ? `${row.duration_min} دقيقة` : '',
                row.cost ? `${row.cost} ر.س` : '',
                formatMedications(row.medications),
                row.treatment,
                row.diagnosis,
                row.visit_type,
                row.time,
                row.date
            ];
            
            cellData.forEach(cellValue => {
                const td = document.createElement('td');
                td.textContent = cellValue || '';
                td.className = 'text-center';
                tr.appendChild(td);
            });
            
            tableBody.appendChild(tr);
        });
    }
    
    /**
     * Render aggregate table (per-dog summary) - RTL column order
     */
    function renderAggregateTable(table) {
        // Arabic headers in RTL order
        const headers = [
            'متوسط المدة (دقيقة)', 'مجموع التكلفة', 'عدد الأدوية',
            'حسب النوع (روتيني/طارئ/تطعيم)', 'عدد الزيارات',
            'الكلب', 'الكود'
        ];
        
        // Create header row
        tableHeaders.innerHTML = '';
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            th.className = 'text-center';
            headerRow.appendChild(th);
        });
        tableHeaders.appendChild(headerRow);
        
        // Create data rows in RTL order
        tableBody.innerHTML = '';
        table.forEach(row => {
            const tr = document.createElement('tr');
            
            // Format visit types breakdown
            const visitTypesStr = Object.entries(row.by_visit_type)
                .map(([type, count]) => `${type}: ${count}`)
                .join(', ');
            
            // Data in RTL order to match headers
            const cellData = [
                row.avg_duration_min ? `${row.avg_duration_min} دقيقة` : '',
                row.cost_sum ? `${row.cost_sum} ر.س` : '',
                row.medications_count || 0,
                visitTypesStr,
                row.visits || 0,
                row.dog_name,
                row.dog_code
            ];
            
            cellData.forEach(cellValue => {
                const td = document.createElement('td');
                td.textContent = cellValue || '';
                td.className = 'text-center';
                tr.appendChild(td);
            });
            
            tableBody.appendChild(tr);
        });
    }
    
    /**
     * Load and display report data
     */
    async function loadReportData() {
        showLoading();
        
        try {
            // Prepare form data
            const formData = new FormData(filterForm);
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value.trim()) {
                    params.append(key, value);
                }
            }
            
            // Add show_kpis checkbox value
            if (showKpisCheck.checked) {
                params.append('show_kpis', '1');
            } else {
                params.append('show_kpis', '0');
            }
            
            const response = await fetch(`/api/reports/breeding/veterinary?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                // FIXED: Better error handling for non-JSON responses
                let errorMessage = 'حدث خطأ في تحميل البيانات';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (parseError) {
                    // If response isn't JSON (like 429 rate limit), show status
                    errorMessage = `خطأ في الخادم (${response.status}): ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            let data;
            try {
                data = await response.json();
                // FIXED: Check if response is empty or malformed
                if (!data || Object.keys(data).length === 0) {
                    throw new Error('لم يتم استلام بيانات صحيحة من الخادم');
                }
            } catch (parseError) {
                console.error('JSON parsing error:', parseError);
                throw new Error('خطأ في تحليل البيانات المستلمة');
            }
            
            hideLoading();
            
            // Check if we have data
            const hasData = (data.granularity === 'day' && data.rows && data.rows.length > 0) ||
                           (data.granularity !== 'day' && data.table && data.table.length > 0);
            
            if (!hasData) {
                showNoData();
                return;
            }
            
            // Show content area
            reportContentArea.style.display = 'block';
            errorMessage.style.display = 'none';
            noDataMessage.style.display = 'none';
            
            // Update KPIs
            updateKPIs(data.kpis);
            
            // Render appropriate table
            if (data.granularity === 'day') {
                renderDailyTable(data.rows);
            } else {
                renderAggregateTable(data.table);
            }
            
        } catch (error) {
            console.error('Error loading report data:', error);
            showError(error.message);
        }
    }
    
    /**
     * Export PDF report
     */
    async function exportPDF() {
        try {
            // Prepare form data
            const formData = new FormData(filterForm);
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value.trim()) {
                    params.append(key, value);
                }
            }
            
            // Add show_kpis checkbox value
            if (showKpisCheck.checked) {
                params.append('show_kpis', '1');
            } else {
                params.append('show_kpis', '0');
            }
            
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التصدير...';
            
            const response = await fetch(`/api/reports/breeding/veterinary/export.pdf?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                // FIXED: Better error handling for PDF export
                let errorMessage = 'حدث خطأ في تصدير التقرير';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (parseError) {
                    errorMessage = `خطأ في الخادم (${response.status}): ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            
            let result;
            try {
                result = await response.json();
            } catch (parseError) {
                throw new Error('خطأ في تحليل استجابة التصدير');
            }
            
            if (result.success) {
                // Create download link
                const link = document.createElement('a');
                link.href = result.file;
                link.download = result.filename;
                link.click();
                
                // Show success message
                alert('تم تصدير التقرير بنجاح');
            } else {
                throw new Error('فشل في تصدير التقرير');
            }
            
        } catch (error) {
            console.error('Error exporting PDF:', error);
            alert(`خطأ في التصدير: ${error.message}`);
        } finally {
            exportBtn.disabled = false;
            exportBtn.innerHTML = '<i class="fas fa-file-pdf me-2"></i>تصدير PDF';
        }
    }
    
    // Event listeners
    rangeTypeSelect.addEventListener('change', toggleDateInputs);
    document.getElementById('project_id').addEventListener('change', loadDogs);
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        loadReportData();
    });
    exportBtn.addEventListener('click', exportPDF);
    
    // Initialize
    toggleDateInputs();
    loadDogs();
    
    // Auto-load if we have initial parameters
    const hasInitialParams = document.getElementById('date').value ||
                            document.getElementById('week_start').value ||
                            document.getElementById('year_month').value ||
                            (document.getElementById('date_from').value && document.getElementById('date_to').value);
    
    if (hasInitialParams) {
        loadReportData();
    }
});