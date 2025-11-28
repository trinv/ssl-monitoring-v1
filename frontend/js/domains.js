/**
 * SSL Certificate Monitoring - Domain Management Functions
 */

// ==================== Domain Loading ====================

async function loadDomains(page = 1) {
    try {
        const data = await fetchDomains(page, currentFilters, currentSortBy, currentSortOrder);

        if (data.domains) {
            currentPage = data.page || 1;
            totalPages = data.total_pages || 1;
            totalDomains = data.total || 0;
            renderDomainTable(data.domains);
            renderPagination();
        } else {
            renderDomainTable(data);
        }
    } catch (error) {
        console.error('Error loading domains:', error);
        const tbody = document.getElementById('domainTableBody');
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Error loading domains</td></tr>';
    }
}

// ==================== Rendering Functions ====================

function renderDomainTable(domains) {
    const tbody = document.getElementById('domainTableBody');

    if (!domains || domains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No domains found</td></tr>';
        document.getElementById('domainCount').textContent = '0 domains';
        return;
    }

    document.getElementById('domainCount').textContent = `${totalDomains} domain${totalDomains !== 1 ? 's' : ''}`;

    tbody.innerHTML = domains.map(d => `
        <tr>
            <td>
                <input type="checkbox" class="domain-checkbox" value="${d.id}">
            </td>
            <td class="domain-cell">${escapeHtml(d.domain)}</td>
            <td>${renderSSLStatusDots(d.status_history)}</td>
            <td>${renderExpiryDate(d.ssl_expiry_date, d.days_until_expiry)}</td>
            <td>${d.scan_time || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-primary mr-1" onclick="checkSingleSSL(${d.id})" title="Check SSL">
                    <i class="fas fa-shield-alt"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteDomain(${d.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    $('[data-toggle="tooltip"]').tooltip();

    document.querySelectorAll('.domain-checkbox').forEach(cb => {
        cb.addEventListener('change', updateBulkActions);
    });
}

function renderSSLStatusDots(history) {
    if (!history || history.length === 0) {
        return '<span class="ssl-dot no-data" title="No scan data"></span>';
    }

    const sortedHistory = [...history].reverse();
    return sortedHistory.slice(0, 5).map(h => {
        const cssClass = h.ssl_status === 'VALID' ? 'valid' : 'invalid';
        const title = `${h.ssl_status} - ${h.scan_time}${h.days_until_expiry !== null ? ` (${h.days_until_expiry} days)` : ''}`;
        return `<span class="ssl-dot ${cssClass}" data-toggle="tooltip" title="${title}"></span>`;
    }).join('');
}

function renderExpiryDate(expiryDate, daysUntilExpiry) {
    if (!expiryDate || daysUntilExpiry === null) {
        return '<span class="badge badge-secondary badge-expiry">N/A</span>';
    }

    let badgeClass = 'badge-success';
    if (daysUntilExpiry < 7) {
        badgeClass = 'badge-danger';
    } else if (daysUntilExpiry < 30) {
        badgeClass = 'badge-warning';
    }

    return `<div class="expiry-container">
        <span class="badge ${badgeClass} badge-expiry">${expiryDate}</span>
        <div class="text-muted small mt-1">${daysUntilExpiry} days left</div>
    </div>`;
}

function renderPagination() {
    const paginationInfo = document.getElementById('paginationInfo');
    const paginationInfoTop = document.getElementById('paginationInfoTop');
    const paginationControls = document.getElementById('paginationControls');
    const paginationControlsTop = document.getElementById('paginationControlsTop');

    const start = totalDomains > 0 ? ((currentPage - 1) * ITEMS_PER_PAGE) + 1 : 0;
    const end = Math.min(currentPage * ITEMS_PER_PAGE, totalDomains);
    const infoText = `Showing ${start} to ${end} of ${totalDomains} entries`;

    paginationInfo.textContent = infoText;
    paginationInfoTop.textContent = infoText;

    let html = '';

    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">Previous</a>
    </li>`;

    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage + 1 < maxButtons) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1); return false;">1</a></li>`;
        if (startPage > 2) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
        </li>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages}); return false;">${totalPages}</a></li>`;
    }

    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>
    </li>`;

    paginationControls.innerHTML = html;
    paginationControlsTop.innerHTML = html;
}

// ==================== Domain CRUD Operations ====================

async function addDomain() {
    const domain = prompt('Enter domain name:');
    if (!domain) return;

    try {
        await createDomain(domain.trim());
        alert('Domain added successfully');
        loadDomains(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding domain');
    }
}

async function addDomainsBulk() {
    $('#bulkAddModal').modal('show');
}

async function bulkAddDomains() {
    const domainsText = document.getElementById('bulkDomainsInput').value;
    if (!domainsText.trim()) {
        alert('Please enter at least one domain');
        return;
    }

    const domains = domainsText.split('\n').map(d => d.trim()).filter(d => d.length > 0);

    try {
        const result = await createDomainsBulk(domains);

        let message = `Added ${result.total_added} domain(s)`;
        if (result.total_failed > 0) {
            message += `\nFailed: ${result.total_failed} domain(s)`;
        }
        alert(message);

        $('#bulkAddModal').modal('hide');
        document.getElementById('bulkDomainsInput').value = '';

        loadDomains(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding domains');
    }
}

async function deleteSingleDomain(domainId) {
    if (!confirm('Are you sure you want to delete this domain?')) return;

    try {
        await deleteDomain(domainId);
        alert('Domain deleted successfully');
        loadDomains(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domain');
    }
}

async function bulkDelete() {
    const selectedCheckboxes = document.querySelectorAll('.domain-checkbox:checked');
    if (selectedCheckboxes.length === 0) {
        alert('Please select at least one domain');
        return;
    }

    const domainIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

    if (!confirm(`Delete ${domainIds.length} selected domain(s)?`)) {
        return;
    }

    try {
        await deleteDomainsBulk(domainIds);
        alert(`Deleted ${domainIds.length} domain(s)`);
        clearSelection();
        loadDomains(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domains');
    }
}

async function bulkDeleteByName() {
    $('#bulkDeleteModal').modal('show');
}

async function bulkDeleteDomains() {
    const domainsText = document.getElementById('bulkDeleteInput').value;
    if (!domainsText.trim()) {
        alert('Please enter at least one domain');
        return;
    }

    const domains = domainsText.split('\n').map(d => d.trim()).filter(d => d.length > 0);

    if (!confirm(`Delete ${domains.length} domain(s)?`)) {
        return;
    }

    try {
        const result = await deleteDomainsByName(domains);

        let message = `Deleted ${result.deleted_count} domain(s)`;
        if (result.not_found_domains.length > 0) {
            message += `\nNot found: ${result.not_found_domains.length} domain(s)`;
        }
        alert(message);

        $('#bulkDeleteModal').modal('hide');
        document.getElementById('bulkDeleteInput').value = '';

        loadDomains(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domains');
    }
}

// ==================== SSL Scanning ====================

async function triggerScan() {
    const button = event.target.closest('button');
    const originalHtml = button.innerHTML;

    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Triggering...';

    try {
        const data = await triggerFullScan();
        alert('Scan triggered successfully! Scanner will start within 5 seconds.');

        setTimeout(() => {
            loadDashboard();
            loadDomains();
        }, SCAN_COMPLETION_WAIT);
    } catch (error) {
        console.error('Error:', error);
        alert('Error triggering scan');
    } finally {
        button.disabled = false;
        button.innerHTML = originalHtml;
    }
}

async function checkSelectedSSL() {
    const selectedCheckboxes = document.querySelectorAll('.domain-checkbox:checked');
    console.log('Selected checkboxes:', selectedCheckboxes.length);

    if (selectedCheckboxes.length === 0) {
        alert('Please select at least one domain');
        return;
    }

    const domainIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));
    console.log('Domain IDs to scan:', domainIds);

    if (!confirm(`Check SSL for ${domainIds.length} selected domain(s)?`)) {
        return;
    }

    try {
        console.log('Sending request to:', `${API_BASE_URL}/scan/domains`);
        console.log('Request body:', { domain_ids: domainIds });

        const data = await triggerDomainsScan(domainIds);
        alert(`SSL scan triggered for ${data.domain_count} domain(s). Scanner will start within 5 seconds.`);

        clearSelection();

        setTimeout(() => {
            loadDashboard();
            loadDomains();
        }, SCAN_COMPLETION_WAIT);
    } catch (error) {
        console.error('Error:', error);
        alert('Error triggering SSL scan');
    }
}

async function checkSingleSSL(domainId) {
    if (!confirm('Check SSL for this domain?')) {
        return;
    }

    try {
        const data = await triggerDomainsScan([domainId]);
        alert(`SSL scan triggered for: ${data.domains[0]}. Scanner will start within 5 seconds.`);

        setTimeout(() => {
            loadDashboard();
            loadDomains();
        }, SCAN_COMPLETION_WAIT);
    } catch (error) {
        console.error('Error:', error);
        alert('Error triggering SSL scan');
    }
}

// ==================== UI Helpers ====================

function changePage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadDomains(currentPage);
}

function sortTable(column) {
    if (currentSortBy === column) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortBy = column;
        currentSortOrder = 'asc';
    }

    updateSortIcons();
    currentPage = 1;
    loadDomains(currentPage);
}

function updateSortIcons() {
    document.querySelectorAll('th i[id^="sort-"]').forEach(icon => {
        icon.className = 'fas fa-sort text-muted';
    });

    const currentIcon = document.getElementById(`sort-${currentSortBy}`);
    if (currentIcon) {
        if (currentSortOrder === 'asc') {
            currentIcon.className = 'fas fa-sort-up text-primary';
        } else {
            currentIcon.className = 'fas fa-sort-down text-primary';
        }
    }
}

function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.domain-checkbox').forEach(cb => {
        cb.checked = checked;
    });
    updateBulkActions();
}

function updateBulkActions() {
    const selectedCount = document.querySelectorAll('.domain-checkbox:checked').length;
    document.getElementById('selectedCount').textContent = selectedCount;

    const bulkActions = document.getElementById('bulkActions');
    if (selectedCount > 0) {
        bulkActions.classList.add('show');
    } else {
        bulkActions.classList.remove('show');
    }
}

function clearSelection() {
    document.getElementById('selectAll').checked = false;
    document.querySelectorAll('.domain-checkbox').forEach(cb => {
        cb.checked = false;
    });
    updateBulkActions();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', function () {
    initDashboard();
    loadDomains(1);
});
