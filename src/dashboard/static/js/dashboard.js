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
// Priority colours (lead scoring) — ordered Low → Critical
const COLORS = {
    low:      '#94a3b8',  // grey
    medium:   '#3b82f6',  // light blue
    high:     '#ea580c',  // dark orange
    critical: '#dc2626',  // dark red
};

// Map with capitalised keys for chart lookups
const PRIORITY_COLORS = {
    Low:      '#94a3b8',
    Medium:   '#3b82f6',
    High:     '#ea580c',
    Critical: '#dc2626',
};

// Canonical ordering (Low → High / Critical)
const PRIORITY_ORDER = ['Low', 'Medium', 'High', 'Critical'];
const RISK_ORDER = ['Low', 'Medium', 'High'];

// Risk colours (churn)
const RISK_COLORS = {
    Low:    '#16a34a',  // dark green
    Medium: '#3b82f6',  // light blue
    High:   '#dc2626',  // dark red
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

// Helper: extract ordered values from a breakdown dict using a fixed key order
function orderedData(breakdown, order) {
    return order.map(key => breakdown[key] || 0);
}

// Chart.js global defaults
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#64748b';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
