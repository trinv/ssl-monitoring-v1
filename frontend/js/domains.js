/**
 * SSL Certificate Monitoring - Domain Management Functions
 */

// ==================== Domain Loading ====================

async function loadDomains(page = 1) {
    const params = new URLSearchParams();

    const search = document.getElementById('searchInput')?.value;
    const sslStatus = document.getElementById('sslStatusFilter')?.value;
    const expiryFilter = document.getElementById('expiryFilter')?.value;

    params.append('page', page);
    params.append('per_page', '100');

    if (search) params.append('search', search);
    if (sslStatus) params.append('ssl_status', sslStatus);
    if (expiryFilter === 'expired_soon') params.append('expired_soon', 'true');

    params.append('sort_by', currentSortBy);
    params.append('sort_order', currentSortOrder);

    try {
        const response = await fetch(`${API_BASE_URL}/domains?${params}`);
        const data = await response.json();

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
                <button class="btn-check-ssl mr-2" onclick="checkSingleSSL(${d.id})" title="Click to check SSL for domain now">
                    <i class="fas fa-shield-alt"></i> Check SSL
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

    const dots = history.slice(0, 5).reverse().map(h => {
        const cssClass = h.ssl_status === 'VALID' ? 'valid' : (h.ssl_status === 'INVALID' ? 'invalid' : 'no-data');
        const statusText = h.ssl_status || 'Unknown';
        const scanTime = h.scan_time || 'N/A';
        const tooltip = `${statusText} - ${scanTime}`;

        return `<span class="ssl-dot ${cssClass}" data-toggle="tooltip" title="${tooltip}"></span>`;
    }).join('');

    return dots || '<span class="ssl-dot no-data" title="No data"></span>';
}

function renderExpiryDate(expiryDate, daysUntil) {
    if (!expiryDate || expiryDate === '-' || expiryDate === 'NO_SSL') {
        return '<span class="badge badge-secondary" style="font-size: 14px; padding: 8px 12px;">N/A</span>';
    }

    if (daysUntil === null || daysUntil === undefined) {
        return `<span class="badge badge-secondary" style="font-size: 14px; padding: 8px 12px;">${escapeHtml(expiryDate)}</span>`;
    }

    const badgeClass = daysUntil < 7 ? 'badge-expired-soon' : 'badge-expired-ok';
    const dateStr = expiryDate.includes('GMT') ? new Date(expiryDate).toISOString().split('T')[0] : expiryDate;

    return `<span class="badge ${badgeClass}">${escapeHtml(dateStr)} - ${daysUntil} days</span>`;
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

// ==================== Modal Functions ====================

function showAddDomainModal() {
    $('#addDomainModal').modal('show');
}

function showBulkAddModal() {
    $('#bulkAddModal').modal('show');
}

function showBulkDeleteMenu() {
    $('#bulkDeleteModal').modal('show');
}

// ==================== Domain CRUD Operations ====================

async function addDomain() {
    const domain = document.getElementById('newDomain').value.trim();
    const notes = document.getElementById('domainNotes').value.trim();

    if (!domain) {
        alert('Please enter a domain');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/domains`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain, notes: notes || null })
        });

        if (response.ok) {
            $('#addDomainModal').modal('hide');
            document.getElementById('newDomain').value = '';
            document.getElementById('domainNotes').value = '';

            alert('Domain added successfully!');
            loadDashboard();
            loadDomains();
        } else {
            const error = await response.json();
            alert(error.detail || 'Error adding domain');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding domain');
    }
}

async function bulkAddDomains() {
    const text = document.getElementById('bulkDomains').value.trim();
    if (!text) {
        alert('Please enter domains');
        return;
    }

    const domains = text.split('\n').map(d => d.trim()).filter(d => d);

    if (domains.length === 0) {
        alert('No valid domains found');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/domains/bulk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domains })
        });

        const result = await response.json();
        alert(`Success!\nAdded: ${result.total_added}\nFailed: ${result.total_failed}`);

        $('#bulkAddModal').modal('hide');
        document.getElementById('bulkDomains').value = '';
        loadDashboard();
        loadDomains();
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding domains');
    }
}

async function deleteDomain(id) {
    if (!confirm('Are you sure you want to delete this domain?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/domains/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadDashboard();
            loadDomains();
        } else {
            alert('Error deleting domain');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domain');
    }
}

async function bulkDelete() {
    const ids = Array.from(document.querySelectorAll('.domain-checkbox:checked'))
        .map(cb => parseInt(cb.value));

    if (ids.length === 0) return;

    if (!confirm(`Are you sure you want to delete ${ids.length} domains?`)) return;

    try {
        const response = await fetch(`${API_BASE_URL}/domains/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain_ids: ids })
        });

        if (response.ok) {
            clearSelection();
            loadDashboard();
            loadDomains();
        } else {
            alert('Error deleting domains');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domains');
    }
}

async function bulkDeleteDomains() {
    const text = document.getElementById('bulkDeleteDomains').value.trim();
    if (!text) {
        alert('Please enter domains to delete');
        return;
    }

    const domains = text.split('\n').map(d => d.trim()).filter(d => d);

    if (domains.length === 0) {
        alert('No valid domains found');
        return;
    }

    if (!confirm(`Are you sure you want to delete ${domains.length} domains?\n\nThis action cannot be undone!`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/domains/bulk-delete-by-name`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domains: domains })
        });

        if (response.ok) {
            const result = await response.json();
            let message = `Successfully deleted ${result.deleted_count} domains!`;

            if (result.not_found_domains && result.not_found_domains.length > 0) {
                message += `\n\nNot found (${result.not_found_domains.length}):\n${result.not_found_domains.slice(0, 10).join('\n')}`;
                if (result.not_found_domains.length > 10) {
                    message += `\n... and ${result.not_found_domains.length - 10} more`;
                }
            }

            alert(message);
            $('#bulkDeleteModal').modal('hide');
            document.getElementById('bulkDeleteDomains').value = '';
            loadDashboard();
            loadDomains();
        } else {
            const error = await response.json();
            alert(error.detail || 'Error deleting domains');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting domains: ' + error.message);
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
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

function applyFilters() {
    const search = document.getElementById('searchInput')?.value || '';
    const sslStatus = document.getElementById('sslStatusFilter')?.value || '';
    const expiryFilter = document.getElementById('expiryFilter')?.value || '';

    currentFilters = {
        search: search,
        sslStatus: sslStatus || null,
        expiredSoon: expiryFilter === 'expired_soon'
    };

    currentPage = 1;
    loadDomains(1);
}

function applyQuickFilter(type) {
    document.getElementById('sslStatusFilter').value = '';
    document.getElementById('expiryFilter').value = '';
    document.getElementById('searchInput').value = '';

    switch(type) {
        case 'valid':
            document.getElementById('sslStatusFilter').value = 'VALID';
            break;
        case 'expired':
            document.getElementById('expiryFilter').value = 'expired_soon';
            break;
        case 'failed':
            document.getElementById('sslStatusFilter').value = 'INVALID';
            break;
    }

    currentPage = 1;
    loadDomains(1);
}

function refreshData() {
    loadDashboard();
    loadDomains();
}

function exportCSV() {
    const sslStatus = document.getElementById('sslStatusFilter')?.value;
    const url = sslStatus ?
        `${API_BASE_URL}/export/csv?ssl_status=${sslStatus}` :
        `${API_BASE_URL}/export/csv`;

    window.location.href = url;
}

// ==================== Initialize ====================

// Initialization moved to index.html to integrate with auth
// Enter key triggers search - setup on document ready
$(document).ready(function() {
    $('#searchInput').on('keypress', function(e) {
        if (e.key === 'Enter') applyFilters();
    });
    updateSortIcons();
});
