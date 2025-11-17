/**
 * Chart Utilities for K9 Reports
 * Provides reusable chart components using Chart.js
 */

// Initialize Chart.js with RTL support
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            rtl: true,
            textDirection: 'rtl',
            labels: {
                font: {
                    family: 'Noto Sans Arabic, sans-serif',
                    size: 12
                }
            }
        },
        tooltip: {
            rtl: true,
            textDirection: 'rtl',
            titleFont: {
                family: 'Noto Sans Arabic, sans-serif'
            },
            bodyFont: {
                family: 'Noto Sans Arabic, sans-serif'
            }
        }
    },
    scales: {
        x: {
            ticks: {
                font: {
                    family: 'Noto Sans Arabic, sans-serif',
                    size: 11
                }
            }
        },
        y: {
            ticks: {
                font: {
                    family: 'Noto Sans Arabic, sans-serif',
                    size: 11
                }
            }
        }
    }
};

/**
 * Create a bar chart
 */
function createBarChart(canvasId, labels, data, label, color = '#667eea') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            ...chartDefaults,
            scales: {
                ...chartDefaults.scales,
                y: {
                    ...chartDefaults.scales.y,
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Create a line chart
 */
function createLineChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets.map(ds => ({
                ...ds,
                tension: 0.3,
                fill: false
            }))
        },
        options: chartDefaults
    });
}

/**
 * Create a pie/doughnut chart
 */
function createPieChart(canvasId, labels, data, colors, type = 'doughnut') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            ...chartDefaults,
            cutout: type === 'doughnut' ? '70%' : 0
        }
    });
}

/**
 * Create a comparison chart (multiple bars)
 */
function createComparisonChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets.map(ds => ({
                ...ds,
                borderWidth: 1,
                borderRadius: 5
            }))
        },
        options: {
            ...chartDefaults,
            scales: {
                ...chartDefaults.scales,
                y: {
                    ...chartDefaults.scales.y,
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Create a trend chart (for time series)
 */
function createTrendChart(canvasId, timeLabels, dataPoints, label, color = '#667eea') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: label,
                data: dataPoints,
                borderColor: color,
                backgroundColor: color + '33',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: chartDefaults
    });
}

/**
 * Export chart as image
 */
function exportChartAsImage(chartInstance, filename = 'chart.png') {
    const link = document.createElement('a');
    link.href = chartInstance.toBase64Image();
    link.download = filename;
    link.click();
}

/**
 * Update chart data dynamically
 */
function updateChartData(chartInstance, newLabels, newData) {
    chartInstance.data.labels = newLabels;
    chartInstance.data.datasets[0].data = newData;
    chartInstance.update();
}

/**
 * Destroy chart instance
 */
function destroyChart(chartInstance) {
    if (chartInstance) {
        chartInstance.destroy();
    }
}

// Color schemes for consistent branding
const colorSchemes = {
    primary: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'],
    success: ['#11998e', '#38ef7d', '#84fab0', '#8fd3f4'],
    warning: ['#f2994a', '#f2c94c', '#ffecd2', '#fcb69f'],
    info: ['#3a7bd5', '#00d2ff', '#a8edea', '#fed6e3'],
    danger: ['#ee0979', '#ff6a00', '#fc4a1a', '#f7b733']
};

/**
 * Show loading state for chart
 */
function showChartLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center" style="height: 300px;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">جاري التحميل...</span>
            </div>
        </div>
    `;
}

/**
 * Show empty state for chart
 */
function showChartEmpty(containerId, message = 'لا توجد بيانات للعرض') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="d-flex flex-column justify-content-center align-items-center text-muted" style="height: 300px;">
            <i class="fas fa-chart-bar fa-3x mb-3 opacity-50"></i>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Show error state for chart
 */
function showChartError(containerId, message = 'حدث خطأ أثناء تحميل البيانات') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="d-flex flex-column justify-content-center align-items-center text-danger" style="height: 300px;">
            <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Load chart data from API endpoint
 */
async function loadChartData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Create chart with loading state and error handling
 */
async function createChartWithLoading(containerId, canvasId, endpoint, chartCreator) {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    // Show loading state
    showChartLoading(containerId);
    
    // Load data
    const result = await loadChartData(endpoint);
    
    if (!result.success) {
        showChartError(containerId, 'فشل تحميل البيانات');
        return null;
    }
    
    const chartData = result.data;
    
    // Check if data is empty
    if (!chartData.data || chartData.data.length === 0 || chartData.data.every(v => v === 0)) {
        showChartEmpty(containerId);
        return null;
    }
    
    // Reset container and add canvas
    container.innerHTML = `<canvas id="${canvasId}"></canvas>`;
    
    // Create chart
    return chartCreator(chartData);
}

/**
 * Format Arabic numbers
 */
function formatArabicNumber(num) {
    const arabicNumerals = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return String(num).replace(/\d/g, (digit) => arabicNumerals[parseInt(digit)]);
}

/**
 * Get color palette for charts (supports light/dark mode)
 */
function getColorPalette(type = 'default') {
    const palettes = {
        default: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#38ef7d'],
        status: {
            draft: '#94a3b8',
            submitted: '#fbbf24',
            approved: '#10b981',
            rejected: '#ef4444',
            needs_revision: '#f97316'
        },
        attendance: {
            present: '#10b981',
            absent: '#ef4444',
            replaced: '#f59e0b'
        },
        dogStatus: ['#10b981', '#3b82f6', '#94a3b8', '#f59e0b', '#ef4444', '#6b7280', '#8b5cf6'],
        roles: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    };
    
    return palettes[type] || palettes.default;
}

/**
 * Create responsive chart container
 */
function createChartContainer(containerId, title, height = '300px') {
    const container = document.getElementById(containerId);
    if (!container) return null;
    
    container.innerHTML = `
        <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white">
                <h6 class="mb-0">${title}</h6>
            </div>
            <div class="card-body">
                <div style="position: relative; height: ${height};">
                    <canvas id="${containerId}-canvas"></canvas>
                </div>
            </div>
        </div>
    `;
    
    return `${containerId}-canvas`;
}

// Export utilities
window.ChartUtils = {
    createBarChart,
    createLineChart,
    createPieChart,
    createComparisonChart,
    createTrendChart,
    exportChartAsImage,
    updateChartData,
    destroyChart,
    showChartLoading,
    showChartEmpty,
    showChartError,
    loadChartData,
    createChartWithLoading,
    formatArabicNumber,
    getColorPalette,
    createChartContainer,
    colorSchemes
};
