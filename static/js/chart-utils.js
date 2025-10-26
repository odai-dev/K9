// Chart.js Utilities for RTL Support

// RTL-aware chart configuration
function createRTLChartConfig(config) {
    if (!config.options) config.options = {};
    if (!config.options.plugins) config.options.plugins = {};
    
    // Set RTL support
    config.options.indexAxis = config.options.indexAxis || 'x';
    
    // Configure legend for RTL
    if (!config.options.plugins.legend) {
        config.options.plugins.legend = {};
    }
    config.options.plugins.legend.rtl = true;
    config.options.plugins.legend.textDirection = 'rtl';
    
    // Configure tooltip for RTL
    if (!config.options.plugins.tooltip) {
        config.options.plugins.tooltip = {};
    }
    config.options.plugins.tooltip.rtl = true;
    config.options.plugins.tooltip.textDirection = 'rtl';
    
    return config;
}

// Default color schemes
const chartColors = {
    primary: '#0d6efd',
    secondary: '#6c757d',
    success: '#198754',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#0dcaf0',
    light: '#f8f9fa',
    dark: '#212529'
};

// Generate color palette
function generateColorPalette(count) {
    const colors = Object.values(chartColors);
    const palette = [];
    
    for (let i = 0; i < count; i++) {
        palette.push(colors[i % colors.length]);
    }
    
    return palette;
}

// Default chart options
const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            display: true,
            position: 'top',
            rtl: true,
            textDirection: 'rtl'
        },
        tooltip: {
            rtl: true,
            textDirection: 'rtl'
        }
    }
};

// Create a simple bar chart
function createBarChart(canvasId, labels, data, label = 'البيانات') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const config = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: generateColorPalette(data.length),
                borderWidth: 1
            }]
        },
        options: defaultChartOptions
    };
    
    return new Chart(ctx, createRTLChartConfig(config));
}

// Create a simple line chart
function createLineChart(canvasId, labels, data, label = 'البيانات') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primary + '20',
                tension: 0.4
            }]
        },
        options: defaultChartOptions
    };
    
    return new Chart(ctx, createRTLChartConfig(config));
}

// Create a simple pie chart
function createPieChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const config = {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: generateColorPalette(data.length)
            }]
        },
        options: defaultChartOptions
    };
    
    return new Chart(ctx, createRTLChartConfig(config));
}
