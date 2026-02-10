/**
 * Shared dashboard JavaScript utilities.
 * Provides common formatting, data refresh, and helper functions.
 */

// Currency formatter
function formatCurrency(value) {
    if (value === null || value === undefined) return '£0';
    if (value >= 1000000) {
        return '£' + (value / 1000000).toFixed(1) + 'M';
    }
    if (value >= 1000) {
        return '£' + (value / 1000).toFixed(0) + 'K';
    }
    return '£' + value.toFixed(0);
}

// Update last updated timestamp
function updateLastUpdated() {
    const el = document.getElementById('last-updated');
    if (el) {
        const now = new Date();
        el.textContent = 'Updated: ' + now.toLocaleTimeString();
    }
}

// Refresh data (reload the current page's data)
function refreshData() {
    // Destroy existing charts to prevent duplicates
    Chart.helpers.each(Chart.instances, function(instance) {
        instance.destroy();
    });

    // Re-trigger page-specific load function
    if (typeof loadDashboard === 'function') loadDashboard();
    if (typeof loadLeadData === 'function') loadLeadData();
    if (typeof loadPipelineData === 'function') loadPipelineData();
    if (typeof loadChurnData === 'function') loadChurnData();
}

// --- Consistent colour palette ---
// Priority colours (lead scoring)
const COLORS = {
    critical: '#dc2626',  // dark red
    high:     '#ea580c',  // dark orange
    medium:   '#3b82f6',  // light blue
    low:      '#94a3b8',  // grey
};

// Risk colours (churn)
const RISK_COLORS = {
    High:   '#dc2626',  // dark red
    Medium: '#3b82f6',  // light blue
    Low:    '#16a34a',  // dark green
};

// Score range colours: Low range -> Critical range
const SCORE_RANGE_COLORS = ['#94a3b8', '#3b82f6', '#ea580c', '#dc2626'];

// Forecast colours
const FORECAST_COLORS = {
    commit:    '#16a34a',
    best_case: '#3b82f6',
    pipeline:  '#94a3b8',
};

// Helper: map an ordered array of labels to colours from a colour map
function mapColors(labels, colorMap) {
    return labels.map(label => colorMap[label] || '#94a3b8');
}

// Chart.js global defaults
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748b';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
