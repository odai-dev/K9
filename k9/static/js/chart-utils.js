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
    colorSchemes
};
