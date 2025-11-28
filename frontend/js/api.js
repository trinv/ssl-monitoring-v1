/**
 * SSL Certificate Monitoring - API Functions
 */

// Dashboard API
async function fetchDashboardSummary() {
    const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
    return await response.json();
}

// Domain APIs
async function fetchDomains(page = 1, filters = {}, sortBy = 'domain', sortOrder = 'asc') {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('per_page', ITEMS_PER_PAGE);
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);

    if (filters.sslStatus) {
        params.append('ssl_status', filters.sslStatus);
    }
    if (filters.expiredSoon) {
        params.append('expired_soon', 'true');
    }
    if (filters.search) {
        params.append('search', filters.search);
    }

    const response = await fetch(`${API_BASE_URL}/domains?${params}`);
    return await response.json();
}

async function createDomain(domain, notes = null) {
    const response = await fetch(`${API_BASE_URL}/domains`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, notes })
    });
    return await response.json();
}

async function createDomainsBulk(domains) {
    const response = await fetch(`${API_BASE_URL}/domains/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domains })
    });
    return await response.json();
}

async function deleteDomain(domainId) {
    const response = await fetch(`${API_BASE_URL}/domains/${domainId}`, {
        method: 'DELETE'
    });
    return await response.json();
}

async function deleteDomainsBulk(domainIds) {
    const response = await fetch(`${API_BASE_URL}/domains/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain_ids: domainIds })
    });
    return await response.json();
}

async function deleteDomainsByName(domains) {
    const response = await fetch(`${API_BASE_URL}/domains/bulk-delete-by-name`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domains })
    });
    return await response.json();
}

// Scan APIs
async function triggerFullScan() {
    const response = await fetch(`${API_BASE_URL}/scan/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    return await response.json();
}

async function triggerDomainsScan(domainIds) {
    const response = await fetch(`${API_BASE_URL}/scan/domains`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain_ids: domainIds })
    });
    return await response.json();
}

// Export API
function exportCSV(sslStatus = null) {
    const url = sslStatus
        ? `${API_BASE_URL}/export/csv?ssl_status=${sslStatus}`
        : `${API_BASE_URL}/export/csv`;
    window.location.href = url;
}
