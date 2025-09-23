/**
 * Trainer Daily Report JavaScript
 * Handles form submission, data rendering, and PDF export
 */

class TrainerDailyReport {
    constructor() {
        this.apiBaseUrl = '/api/reports/training';
        this.currentData = null;
        this.init();
    }

    init() {
        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('date').value = today;

        // Bind event handlers
        document.getElementById('updateReport').addEventListener('click', () => this.loadReport());
        document.getElementById('exportPdf').addEventListener('click', () => this.exportPdf());

        // Load initial data
        this.loadProjects();
        this.loadTrainers();
        this.loadDogs();
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects', {
                credentials: 'include'
            });
            if (response.ok) {
                const projects = await response.json();
                const select = document.getElementById('project_id');
                projects.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.id;
                    option.textContent = project.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading projects:', error.message);
            }
        }
    }

    async loadTrainers() {
        try {
            const response = await fetch('/api/employees?role=TRAINER', {
                credentials: 'include'
            });
            if (response.ok) {
                const trainers = await response.json();
                const select = document.getElementById('trainer_id');
                trainers.forEach(trainer => {
                    const option = document.createElement('option');
                    option.value = trainer.id;
                    option.textContent = trainer.full_name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            if (error && error.message) {
                console.error('Error loading trainers:', error.message);
            }
        }
    }

    async loadDogs() {
        try {
            const response = await fetch('/api/dogs', {
                credentials: 'include'
            });
            if (response.ok) {
                const dogs = await response.json();
                console.log('Dogs loaded successfully:', dogs);
                const select = document.getElementById('dog_id');
                dogs.forEach(dog => {
                    const option = document.createElement('option');
                    option.value = dog.id;
                    option.textContent = dog.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading dogs:', error);
        }
    }

    getFilters() {
        return {
            project_id: document.getElementById('project_id').value || null,
            date: document.getElementById('date').value,
            trainer_id: document.getElementById('trainer_id').value || null,
            dog_id: document.getElementById('dog_id').value || null,
            category: document.getElementById('category').value || null
        };
    }

    showLoading() {
        document.getElementById('loadingMessage').style.display = 'block';
        document.getElementById('errorMessage').style.display = 'none';
        document.getElementById('noDataMessage').style.display = 'none';
        document.getElementById('kpiRow').style.display = 'none';
        document.getElementById('sessionsCard').style.display = 'none';
        document.getElementById('summaryCard').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loadingMessage').style.display = 'none';
    }

    showError(message) {
        document.getElementById('errorText').textContent = message;
        document.getElementById('errorMessage').style.display = 'block';
        this.hideLoading();
    }

    showNoData() {
        document.getElementById('noDataMessage').style.display = 'block';
        this.hideLoading();
    }

    async loadReport() {
        const filters = this.getFilters();
        
        if (!filters.date) {
            this.showError('يرجى تحديد التاريخ');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/run/trainer-daily`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(filters)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'خطأ في الخادم');
            }

            this.currentData = data;
            
            if (data.sessions.length === 0) {
                this.showNoData();
            } else {
                this.renderReport(data);
            }

        } catch (error) {
            if (error && error.message) {
                this.showError(error.message);
            }
        }
    }

    renderReport(data) {
        this.hideLoading();
        
        // Show KPIs
        document.getElementById('totalSessions').textContent = data.kpis.total_sessions;
        document.getElementById('uniqueDogs').textContent = data.kpis.unique_dogs;
        document.getElementById('uniqueTrainers').textContent = data.kpis.unique_trainers;
        document.getElementById('totalDuration').textContent = data.kpis.total_duration_min;
        document.getElementById('avgRating').textContent = data.kpis.avg_success_rating;
        
        // Render sessions table
        this.renderSessionsTable(data.sessions);
        
        // Render summary table
        this.renderSummaryTable(data.summary_by_dog);
        
        // Show sections
        document.getElementById('kpiRow').style.display = 'flex';
        document.getElementById('sessionsCard').style.display = 'block';
        document.getElementById('summaryCard').style.display = 'block';
    }

    renderSessionsTable(sessions) {
        const tbody = document.getElementById('sessionsTableBody');
        tbody.innerHTML = '';

        sessions.forEach(session => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="text-align: right;">${session.notes}</td>
                <td style="text-align: right;">${session.equipment}</td>
                <td style="text-align: right;">${session.weather}</td>
                <td style="text-align: right;">${session.location}</td>
                <td style="text-align: center;">${session.success_rating}</td>
                <td style="text-align: center;">${session.duration_min}</td>
                <td style="text-align: right;">${session.subject}</td>
                <td style="text-align: right;">${session.category_ar}</td>
                <td style="text-align: right;">${session.dog_name}</td>
                <td style="text-align: right;">${session.trainer_name}</td>
                <td style="text-align: center;">${session.time}</td>
            `;
            tbody.appendChild(row);
        });
    }

    renderSummaryTable(summaryData) {
        const tbody = document.getElementById('summaryTableBody');
        tbody.innerHTML = '';

        summaryData.forEach(item => {
            // Format categories breakdown
            const categoriesText = Object.entries(item.categories_breakdown)
                .filter(([_, count]) => count > 0)
                .map(([category, count]) => `${category}: ${count}`)
                .join(', ');

            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="text-align: right;">${categoriesText}</td>
                <td style="text-align: center;">${item.avg_success_rating}</td>
                <td style="text-align: center;">${item.total_duration_min}</td>
                <td style="text-align: center;">${item.sessions_count}</td>
                <td style="text-align: right;">${item.dog_name}</td>
            `;
            tbody.appendChild(row);
        });
    }

    async exportPdf() {
        if (!this.currentData) {
            this.showError('يرجى تحديث التقرير أولاً');
            return;
        }

        const filters = this.getFilters();

        try {
            const response = await fetch(`${this.apiBaseUrl}/export/pdf/trainer-daily`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filters)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'خطأ في التصدير');
            }

            // Open PDF in new tab
            window.open(`/${data.path}`, '_blank');

        } catch (error) {
            if (error && error.message) {
                this.showError(error.message);
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TrainerDailyReport();
});