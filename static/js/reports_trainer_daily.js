document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const projectSelect = document.getElementById('project_id');
    const trainerSelect = document.getElementById('trainer_id');
    const dogSelect = document.getElementById('dog_id');
    const categorySelect = document.getElementById('category');
    const updateBtn = document.getElementById('updateReport');
    const exportBtn = document.getElementById('exportPdf');
    const reportContentArea = document.getElementById('report-content-area');
    const tableBody = document.querySelector('#trainer-daily-table tbody');
    const emptyState = document.getElementById('empty-state');
    const tableLoading = document.getElementById('table-loading');

    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;

    loadFilters();

    updateBtn.addEventListener('click', loadReport);
    exportBtn.addEventListener('click', exportPdf);

    async function loadFilters() {
        try {
            const projectsRes = await fetch('/api/projects');
            if (projectsRes.ok) {
                const projects = await projectsRes.json();
                projects.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.name || p.code;
                    projectSelect.appendChild(opt);
                });
            }

            const trainersRes = await fetch('/api/trainers');
            if (trainersRes.ok) {
                const trainers = await trainersRes.json();
                trainers.forEach(t => {
                    const opt = document.createElement('option');
                    opt.value = t.id;
                    opt.textContent = t.name;
                    trainerSelect.appendChild(opt);
                });
            }

            const dogsRes = await fetch('/api/dogs');
            if (dogsRes.ok) {
                const dogs = await dogsRes.json();
                dogs.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.id;
                    opt.textContent = d.name || d.code;
                    dogSelect.appendChild(opt);
                });
            }
        } catch (e) {
            console.error('Error loading filters:', e);
        }
    }

    async function loadReport() {
        const date = dateInput.value;
        if (!date) {
            alert('يرجى تحديد التاريخ');
            return;
        }

        tableLoading.classList.remove('d-none');
        emptyState.classList.add('d-none');
        tableBody.innerHTML = '';
        reportContentArea.style.display = 'block';

        try {
            const response = await fetch('/api/reports/training/run/trainer-daily', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: date,
                    project_id: projectSelect.value || null,
                    trainer_id: trainerSelect.value || null,
                    dog_id: dogSelect.value || null,
                    category: categorySelect.value || null
                })
            });

            tableLoading.classList.add('d-none');

            if (!response.ok) {
                const errData = await response.json();
                alert(errData.error || 'حدث خطأ أثناء تحميل التقرير');
                return;
            }

            const data = await response.json();
            renderReport(data);
        } catch (e) {
            tableLoading.classList.add('d-none');
            console.error('Error loading report:', e);
            alert('حدث خطأ أثناء تحميل التقرير');
        }
    }

    function renderReport(data) {
        document.getElementById('total-sessions').textContent = data.summary?.total_sessions || data.rows?.length || 0;
        document.getElementById('unique-dogs').textContent = data.summary?.unique_dogs || 0;
        document.getElementById('unique-trainers').textContent = data.summary?.unique_trainers || 0;
        document.getElementById('avg-score').textContent = data.summary?.avg_score ? data.summary.avg_score.toFixed(1) : '0';
        document.getElementById('date-display').textContent = data.date || dateInput.value;
        document.getElementById('project-display').textContent = data.project_name || 'جميع المشاريع';

        const rows = data.rows || [];
        if (rows.length === 0) {
            emptyState.classList.remove('d-none');
            return;
        }

        emptyState.classList.add('d-none');
        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="text-center">${row.date || '-'}</td>
                <td class="text-center">${row.trainer_name || '-'}</td>
                <td class="text-center">${row.dog_name || '-'}</td>
                <td class="text-center">${row.dog_code || '-'}</td>
                <td class="text-center">${row.category || '-'}</td>
                <td class="text-center">${row.exercise || '-'}</td>
                <td class="text-center">${row.score !== null ? row.score : '-'}</td>
                <td class="text-center">${row.notes || '-'}</td>
                <td class="text-center">${row.created_at || '-'}</td>
            `;
            tableBody.appendChild(tr);
        });
    }

    async function exportPdf() {
        const date = dateInput.value;
        if (!date) {
            alert('يرجى تحديد التاريخ');
            return;
        }

        try {
            const response = await fetch('/api/reports/training/export/pdf/trainer-daily', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: date,
                    project_id: projectSelect.value || null,
                    trainer_id: trainerSelect.value || null,
                    dog_id: dogSelect.value || null,
                    category: categorySelect.value || null
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                alert(errData.error || 'حدث خطأ أثناء تصدير التقرير');
                return;
            }

            const data = await response.json();
            if (data.path) {
                window.open(data.path, '_blank');
            }
        } catch (e) {
            console.error('Error exporting PDF:', e);
            alert('حدث خطأ أثناء تصدير التقرير');
        }
    }
});
