/**
 * SSL Certificate Monitoring - Dashboard Functions
 */

// Load and display dashboard summary
async function loadDashboard() {
    try {
        const data = await fetchDashboardSummary();

        document.getElementById('totalDomains').textContent = data.total_domains || 0;
        document.getElementById('sslValidCount').textContent = data.ssl_valid_count || 0;
        document.getElementById('expiredSoonCount').textContent = data.expired_soon_count || 0;
        document.getElementById('failedCount').textContent = data.failed_count || 0;

        if (data.last_scan_time) {
            const lastScan = new Date(data.last_scan_time);
            document.getElementById('lastScan').textContent = lastScan.toLocaleString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        } else {
            document.getElementById('lastScan').textContent = 'Never';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Apply filter from dashboard cards
function applyFilter(filterType, value) {
    currentPage = 1;

    switch (filterType) {
        case 'all':
            currentFilters.sslStatus = null;
            currentFilters.expiredSoon = false;
            break;
        case 'valid':
            currentFilters.sslStatus = SSL_STATUS_OPTIONS.VALID;
            currentFilters.expiredSoon = false;
            break;
        case 'expired_soon':
            currentFilters.sslStatus = null;
            currentFilters.expiredSoon = true;
            break;
        case 'invalid':
            currentFilters.sslStatus = SSL_STATUS_OPTIONS.INVALID;
            currentFilters.expiredSoon = false;
            break;
    }

    loadDomains(currentPage);
}

// Initialize dashboard
function initDashboard() {
    loadDashboard();

    // Auto-refresh dashboard every 30 seconds
    setInterval(loadDashboard, DASHBOARD_REFRESH_INTERVAL);
}
