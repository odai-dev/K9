/**
 * Veterinary Daily Report JavaScript
 */

let currentReportData = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    setDefaultDate();
    showNoDataMessage();
});

function initializeEventListeners() {
    // Update button
    document.getElementById('updateBtn').addEventListener('click', loadReport);
    
    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportPDF);
    
    // Project change to load vets and dogs
    document.getElementById('projectSelect').addEventListener('change', function() {
        loadVets();
        loadDogs();
        hideReport();
    });
    
    // Auto-update when filters change (optional)
    ['vetSelect', 'dogSelect', 'visitTypeSelect'].forEach(id => {
        document.getElementById(id).addEventListener('change', function() {
            if (currentReportData) {
                loadReport();
            }
        });
    });
}

function setDefaultDate() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('dateInput').value = today;
}

function showNoDataMessage() {
    document.getElementById('noDataMessage').style.display = 'block';
    document.getElementById('reportTable').style.display = 'none';
    document.getElementById('emptyDataMessage').style.display = 'none';
    document.getElementById('kpisRow').style.display = 'none';
    document.getElementById('exportBtn').disabled = true;
}

function hideReport() {
    document.getElementById('reportTable').style.display = 'none';
    document.getElementById('emptyDataMessage').style.display = 'none';
    document.getElementById('kpisRow').style.display = 'none';
    document.getElementById('exportBtn').disabled = true;
    currentReportData = null;
}

function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('noDataMessage').style.display = 'none';
    document.getElementById('reportTable').style.display = 'none';
    document.getElementById('emptyDataMessage').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function loadVets() {
    const projectId = document.getElementById('projectSelect').value;
    const vetSelect = document.getElementById('vetSelect');
    
    // Clear current options
    vetSelect.innerHTML = '<option value="">جميع الأطباء</option>';
    
    if (!projectId) return;
    
    fetch(`/api/reports/veterinary/data/vets?project_id=${projectId}`)
        .then(response => response.json())
        .then(vets => {
            vets.forEach(vet => {
                const option = document.createElement('option');
                option.value = vet.id;
                option.textContent = vet.name;
                vetSelect.appendChild(option);
            });
        })
        .catch(error => {
            if (error && error.message) {
                console.error('Error loading vets:', error.message);
            }
        });
}

function loadDogs() {
    const projectId = document.getElementById('projectSelect').value;
    const dogSelect = document.getElementById('dogSelect');
    
    // Clear current options
    dogSelect.innerHTML = '<option value="">جميع الكلاب</option>';
    
    if (!projectId) return;
    
    fetch(`/api/reports/veterinary/data/dogs?project_id=${projectId}`)
        .then(response => response.json())
        .then(dogs => {
            dogs.forEach(dog => {
                const option = document.createElement('option');
                option.value = dog.id;
                option.textContent = `${dog.name} (${dog.breed || 'غير محدد'})`;
                dogSelect.appendChild(option);
            });
        })
        .catch(error => {
            if (error && error.message) {
                console.error('Error loading dogs:', error.message);
            }
        });
}

function loadReport() {
    const projectId = document.getElementById('projectSelect').value;
    const date = document.getElementById('dateInput').value;
    
    if (!projectId || !date) {
        alert('يرجى اختيار المشروع والتاريخ');
        return;
    }
    
    const requestData = {
        project_id: projectId,
        date: date,
        vet_id: document.getElementById('vetSelect').value || null,
        dog_id: document.getElementById('dogSelect').value || null,
        visit_type: document.getElementById('visitTypeSelect').value || null
    };
    
    showLoading();
    
    fetch('/api/reports/veterinary/run/daily', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        currentReportData = data;
        displayReport(data);
    })
    .catch(error => {
        hideLoading();
        if (error && error.message) {
            console.error('Error loading report:', error.message);
            alert('حدث خطأ أثناء تحميل التقرير');
        }
    });
}

function displayReport(data) {
    // Update KPIs
    updateKPIs(data.kpis);
    
    // Update report info
    document.getElementById('reportInfo').textContent = 
        `${data.day_name_ar} - ${data.date_ar}`;
    
    if (data.visits && data.visits.length > 0) {
        // Show table with data
        displayVisitsTable(data.visits);
        document.getElementById('reportTable').style.display = 'block';
        document.getElementById('emptyDataMessage').style.display = 'none';
        document.getElementById('exportBtn').disabled = false;
    } else {
        // Show empty message
        document.getElementById('reportTable').style.display = 'none';
        document.getElementById('emptyDataMessage').style.display = 'block';
        document.getElementById('exportBtn').disabled = true;
    }
    
    document.getElementById('noDataMessage').style.display = 'none';
    document.getElementById('kpisRow').style.display = 'flex';
}

function updateKPIs(kpis) {
    document.getElementById('totalVisits').textContent = kpis.total_visits;
    document.getElementById('uniqueDogs').textContent = kpis.unique_dogs;
    document.getElementById('totalCost').textContent = `${kpis.total_cost} ر.س`;
    document.getElementById('emergencies').textContent = kpis.emergencies;
    document.getElementById('vaccinations').textContent = kpis.vaccinations;
}

function displayVisitsTable(visits) {
    const tbody = document.getElementById('reportTableBody');
    tbody.innerHTML = '';
    
    visits.forEach(visit => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${visit.time}</td>
            <td>${visit.dog_name}</td>
            <td>${visit.breed}</td>
            <td>${visit.vet_name}</td>
            <td><span class="badge bg-info">${visit.visit_type_ar}</span></td>
            <td>${visit.diagnosis}</td>
            <td>${visit.treatment}</td>
            <td>${visit.medications}</td>
            <td>${visit.cost ? visit.cost.toFixed(2) + ' ر.س' : ''}</td>
            <td>${visit.location}</td>
            <td>${visit.weather}</td>
            <td>${visit.vital_signs}</td>
            <td>${visit.notes}</td>
        `;
        
        tbody.appendChild(row);
    });
}

function exportPDF() {
    if (!currentReportData) {
        alert('لا توجد بيانات للتصدير');
        return;
    }
    
    const requestData = {
        project_id: currentReportData.project_id,
        date: currentReportData.date,
        vet_id: currentReportData.filters_applied.vet_id,
        dog_id: currentReportData.filters_applied.dog_id,
        visit_type: currentReportData.filters_applied.visit_type
    };
    
    fetch('/api/reports/veterinary/export/pdf/daily', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `veterinary_daily_${currentReportData.date}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        if (error && error.message) {
            console.error('Error exporting PDF:', error.message);
            alert('حدث خطأ أثناء تصدير PDF');
        }
    });
}