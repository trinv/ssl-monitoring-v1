# 📝 FRONTEND IMPLEMENTATION GUIDE

## File cần tạo: frontend/index.html

Frontend hiện tại (20KB) cần được thay thế hoàn toàn với SSL monitoring UI.

---

## 🎨 COMPLETE HTML TEMPLATE

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SSL Certificate Monitor</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,400i,700&display=fallback">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css">
    <style>
        .ssl-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 3px;
            cursor: pointer;
        }
        .ssl-dot.valid { background-color: #28a745; }
        .ssl-dot.invalid { background-color: #dc3545; }
        .badge-expired-soon { background-color: #dc3545 !important; }
        .badge-expired-ok { background-color: #28a745 !important; }
        .badge-https-2xx { background-color: #28a745 !important; }
        .badge-https-3xx { background-color: #ffc107 !important; }
        .badge-https-4xx, .badge-https-5xx { background-color: #dc3545 !important; }
    </style>
</head>
<body class="hold-transition sidebar-mini">
<div class="wrapper">
    <!-- Navbar -->
    <nav class="main-header navbar navbar-expand navbar-white navbar-light">
        <ul class="navbar-nav">
            <li class="nav-item">
                <a class="nav-link" data-widget="pushmenu" href="#"><i class="fas fa-bars"></i></a>
            </li>
            <li class="nav-item d-none d-sm-inline-block">
                <a href="index.html" class="nav-link">Dashboard</a>
            </li>
        </ul>
    </nav>

    <!-- Sidebar -->
    <aside class="main-sidebar sidebar-dark-primary elevation-4">
        <a href="index.html" class="brand-link">
            <i class="fas fa-shield-alt brand-image ml-3"></i>
            <span class="brand-text font-weight-light">SSL Monitor</span>
        </a>
        <div class="sidebar">
            <nav class="mt-2">
                <ul class="nav nav-pills nav-sidebar flex-column">
                    <li class="nav-item">
                        <a href="#" class="nav-link active">
                            <i class="nav-icon fas fa-tachometer-alt"></i>
                            <p>Dashboard</p>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" class="nav-link" onclick="showAddDomainModal()">
                            <i class="nav-icon fas fa-plus-circle"></i>
                            <p>Add Domain</p>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" class="nav-link" onclick="showBulkAddModal()">
                            <i class="nav-icon fas fa-list"></i>
                            <p>Bulk Add</p>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a href="#" class="nav-link" onclick="exportCSV()">
                            <i class="nav-icon fas fa-download"></i>
                            <p>Export CSV</p>
                        </a>
                    </li>
                </ul>
            </nav>
        </div>
    </aside>

    <!-- Content Wrapper -->
    <div class="content-wrapper">
        <div class="content-header">
            <div class="container-fluid">
                <h1 class="m-0">SSL Certificate Monitor</h1>
            </div>
        </div>

        <section class="content">
            <div class="container-fluid">
                <!-- Stats Cards Row -->
                <div class="row">
                    <!-- Total Domains -->
                    <div class="col-lg-3 col-6">
                        <div class="small-box bg-info">
                            <div class="inner">
                                <h3 id="totalDomains">0</h3>
                                <p>Total Domains</p>
                            </div>
                            <div class="icon">
                                <i class="fas fa-globe"></i>
                            </div>
                        </div>
                    </div>

                    <!-- SSL Valid -->
                    <div class="col-lg-3 col-6">
                        <div class="small-box bg-success">
                            <div class="inner">
                                <h3 id="sslValidCount">0</h3>
                                <p>SSL Valid</p>
                            </div>
                            <div class="icon">
                                <i class="fas fa-check-circle"></i>
                            </div>
                        </div>
                    </div>

                    <!-- Expired Soon -->
                    <div class="col-lg-3 col-6">
                        <div class="small-box bg-warning">
                            <div class="inner">
                                <h3 id="expiredSoonCount">0</h3>
                                <p>Expired Soon (&lt;7 days)</p>
                            </div>
                            <div class="icon">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                        </div>
                    </div>

                    <!-- Failed -->
                    <div class="col-lg-3 col-6">
                        <div class="small-box bg-danger">
                            <div class="inner">
                                <h3 id="failedCount">0</h3>
                                <p>Failed</p>
                            </div>
                            <div class="icon">
                                <i class="fas fa-times-circle"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Filters Card -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Filters & Search</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="form-group">
                                    <label>Search Domain</label>
                                    <input type="text" id="searchInput" class="form-control" placeholder="example.com">
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="form-group">
                                    <label>Sort By</label>
                                    <select id="sortBySelect" class="form-control">
                                        <option value="domain">Domain (A-Z)</option>
                                        <option value="ssl_status">SSL Status</option>
                                        <option value="expiry">Days to Expiry</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="form-group">
                                    <label>SSL Status</label>
                                    <select id="sslStatusFilter" class="form-control">
                                        <option value="">All</option>
                                        <option value="valid">Valid</option>
                                        <option value="invalid">Invalid</option>
                                        <option value="no_ssl">No SSL</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="form-group">
                                    <label>Expiry Status</label>
                                    <select id="expiryFilter" class="form-control">
                                        <option value="">All</option>
                                        <option value="expired_soon">Expired Soon</option>
                                        <option value="valid">Valid</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-2">
                                <div class="form-group">
                                    <label>HTTPS Status</label>
                                    <select id="httpsStatusFilter" class="form-control">
                                        <option value="">All</option>
                                        <option value="2">2xx Success</option>
                                        <option value="3">3xx Redirect</option>
                                        <option value="4">4xx Client Error</option>
                                        <option value="5">5xx Server Error</option>
                                        <option value="0">Failed</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-1">
                                <div class="form-group">
                                    <label>&nbsp;</label>
                                    <button type="button" class="btn btn-primary btn-block" onclick="applyFilters()">
                                        <i class="fas fa-search"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Domain List Card -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Domain List</h3>
                        <div class="card-tools">
                            <button type="button" class="btn btn-sm btn-danger" id="bulkDeleteBtn" style="display:none;" onclick="bulkDelete()">
                                <i class="fas fa-trash"></i> Delete Selected
                            </button>
                        </div>
                    </div>
                    <div class="card-body p-0">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th style="width: 40px;"><input type="checkbox" id="selectAll" onclick="toggleSelectAll()"></th>
                                    <th>Domain</th>
                                    <th style="width: 150px;">SSL Status History</th>
                                    <th style="width: 180px;">Expired on</th>
                                    <th style="width: 100px;">HTTPS Status</th>
                                    <th>Redirect to</th>
                                    <th style="width: 150px;">Last Scan</th>
                                    <th style="width: 80px;">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="domainTableBody">
                                <tr>
                                    <td colspan="8" class="text-center">
                                        <div class="spinner-border text-primary"></div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    </div>

    <footer class="main-footer">
        <strong>SSL Certificate Monitor v2.0</strong>
        <div class="float-right">Server: YOUR_IP_ADDRESS:8080</div>
    </footer>
</div>

<!-- Modals -->
<div class="modal fade" id="addDomainModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title">Add Domain</h4>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Domain Name</label>
                    <input type="text" class="form-control" id="newDomain" placeholder="example.com">
                </div>
                <div class="form-group">
                    <label>Notes (optional)</label>
                    <textarea class="form-control" id="domainNotes" rows="2"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="addDomain()">Add</button>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="bulkAddModal">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h4 class="modal-title">Bulk Add Domains</h4>
                <button type="button" class="close" data-dismiss="modal">&times;</button>
            </div>
            <div class="modal-body">
                <p>Paste domain list (one per line):</p>
                <textarea class="form-control" id="bulkDomains" rows="10" placeholder="example1.com
example2.com
example3.com"></textarea>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="bulkAddDomains()">Add All</button>
            </div>
        </div>
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>

<script>
const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8080/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadDomains();
    setInterval(loadDashboard, 60000); // Refresh every minute
    
    // Initialize Bootstrap tooltips
    $('[data-toggle="tooltip"]').tooltip();
});

// Load dashboard summary
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
        const data = await response.json();
        
        document.getElementById('totalDomains').textContent = data.total_domains;
        document.getElementById('sslValidCount').textContent = data.ssl_valid_count;
        document.getElementById('expiredSoonCount').textContent = data.expired_soon_count;
        document.getElementById('failedCount').textContent = data.failed_count;
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load domains with current filters
async function loadDomains() {
    const params = new URLSearchParams();
    
    const search = document.getElementById('searchInput')?.value;
    const sortBy = document.getElementById('sortBySelect')?.value || 'domain';
    const sslStatus = document.getElementById('sslStatusFilter')?.value;
    const expiryFilter = document.getElementById('expiryFilter')?.value;
    const httpsStatus = document.getElementById('httpsStatusFilter')?.value;
    
    params.append('sort_by', sortBy);
    params.append('limit', '100');
    
    if (search) params.append('search', search);
    if (sslStatus) params.append('ssl_status', sslStatus);
    if (expiryFilter === 'expired_soon') params.append('expired_soon', 'true');
    if (httpsStatus) {
        // Convert category to specific status
        const statusMap = {
            '2': '200', '3': '301', '4': '404', '5': '500', '0': '0'
        };
        if (statusMap[httpsStatus]) {
            params.append('https_status', statusMap[httpsStatus]);
        }
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/domains?${params}`);
        const domains = await response.json();
        
        renderDomainTable(domains);
    } catch (error) {
        console.error('Error loading domains:', error);
        const tbody = document.getElementById('domainTableBody');
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-danger">Error loading domains</td></tr>';
    }
}

// Render domain table
function renderDomainTable(domains) {
    const tbody = document.getElementById('domainTableBody');
    
    if (domains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No domains found</td></tr>';
        return;
    }
    
    tbody.innerHTML = domains.map(d => `
        <tr>
            <td><input type="checkbox" class="domain-checkbox" value="${d.id}"></td>
            <td>${d.domain}</td>
            <td>${renderSSLStatusDots(d.status_history)}</td>
            <td>${renderExpiryDate(d.ssl_expiry_date, d.days_until_expiry)}</td>
            <td>${renderHTTPSStatus(d.https_status)}</td>
            <td>${d.redirect_url ? `<small>${d.redirect_url}</small>` : '-'}</td>
            <td>${formatDateTime(d.scan_time)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteDomain(${d.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    // Re-initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Update checkbox handlers
    document.querySelectorAll('.domain-checkbox').forEach(cb => {
        cb.addEventListener('change', updateBulkDeleteButton);
    });
}

// Render SSL status dots (last 5 scans)
function renderSSLStatusDots(history) {
    if (!history || history.length === 0) {
        return '<span class="text-muted">No data</span>';
    }
    
    return history.slice(0, 5).map(h => {
        const cssClass = h.ssl_status === 'valid' ? 'valid' : 'invalid';
        const tooltip = `${h.ssl_status.toUpperCase()}\\n${h.days_until_expiry || 'N/A'} days\\n${formatDateTime(h.scan_time)}`;
        
        return `<span class="ssl-dot ${cssClass}" data-toggle="tooltip" title="${tooltip}"></span>`;
    }).join('');
}

// Render expiry date with color coding
function renderExpiryDate(expiryDate, daysUntil) {
    if (!expiryDate) {
        return '<span class="badge badge-secondary">N/A</span>';
    }
    
    const badgeClass = daysUntil < 7 ? 'badge-expired-soon' : 'badge-expired-ok';
    const dateStr = new Date(expiryDate).toISOString().split('T')[0];
    
    return `<span class="badge ${badgeClass}">${dateStr}<br>(${daysUntil} days)</span>`;
}

// Render HTTPS status code with color
function renderHTTPSStatus(status) {
    if (!status || status === 0) {
        return '<span class="badge badge-https-5xx">Failed</span>';
    }
    
    let badgeClass = 'badge-secondary';
    if (status >= 200 && status < 300) badgeClass = 'badge-https-2xx';
    else if (status >= 300 && status < 400) badgeClass = 'badge-https-3xx';
    else if (status >= 400 && status < 500) badgeClass = 'badge-https-4xx';
    else if (status >= 500) badgeClass = 'badge-https-5xx';
    
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

// Format datetime
function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('en-GB', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Apply filters
function applyFilters() {
    loadDomains();
}

// Modal functions
function showAddDomainModal() {
    $('#addDomainModal').modal('show');
}

function showBulkAddModal() {
    $('#bulkAddModal').modal('show');
}

// Add single domain
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
            body: JSON.stringify({ domain, notes })
        });
        
        if (response.ok) {
            $('#addDomainModal').modal('hide');
            document.getElementById('newDomain').value = '';
            document.getElementById('domainNotes').value = '';
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

// Bulk add domains
async function bulkAddDomains() {
    const text = document.getElementById('bulkDomains').value.trim();
    if (!text) {
        alert('Please enter domains');
        return;
    }
    
    const domains = text.split('\\n').map(d => d.trim()).filter(d => d);
    
    try {
        const response = await fetch(`${API_BASE_URL}/domains/bulk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domains })
        });
        
        const result = await response.json();
        alert(`Added: ${result.total_added}, Failed: ${result.total_failed}`);
        $('#bulkAddModal').modal('hide');
        document.getElementById('bulkDomains').value = '';
        loadDashboard();
        loadDomains();
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding domains');
    }
}

// Delete single domain
async function deleteDomain(id) {
    if (!confirm('Delete this domain?')) return;
    
    try {
        await fetch(`${API_BASE_URL}/domains/${id}`, { method: 'DELETE' });
        loadDashboard();
        loadDomains();
    } catch (error) {
        console.error('Error:', error);
    }
}

// Select all checkbox
function toggleSelectAll() {
    const checked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.domain-checkbox').forEach(cb => {
        cb.checked = checked;
    });
    updateBulkDeleteButton();
}

// Update bulk delete button visibility
function updateBulkDeleteButton() {
    const selected = document.querySelectorAll('.domain-checkbox:checked').length;
    const btn = document.getElementById('bulkDeleteBtn');
    btn.style.display = selected > 0 ? 'inline-block' : 'none';
    btn.textContent = `Delete Selected (${selected})`;
}

// Bulk delete
async function bulkDelete() {
    const ids = Array.from(document.querySelectorAll('.domain-checkbox:checked'))
        .map(cb => parseInt(cb.value));
    
    if (ids.length === 0) return;
    if (!confirm(`Delete ${ids.length} domains?`)) return;
    
    try {
        await fetch(`${API_BASE_URL}/domains/bulk-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain_ids: ids })
        });
        document.getElementById('selectAll').checked = false;
        loadDashboard();
        loadDomains();
    } catch (error) {
        console.error('Error:', error);
    }
}

// Export CSV
function exportCSV() {
    const sslStatus = document.getElementById('sslStatusFilter')?.value;
    const url = sslStatus ? 
        `${API_BASE_URL}/export/csv?ssl_status=${sslStatus}` :
        `${API_BASE_URL}/export/csv`;
    window.location.href = url;
}
</script>
</body>
</html>
```

---

## ✅ IMPLEMENTATION CHECKLIST

1. Replace `/mnt/user-data/outputs/domain-monitor/frontend/index.html` với code trên
2. Test dashboard loads correctly
3. Test filters work
4. Test SSL status dots show with tooltips
5. Test expiry dates show with colors
6. Test HTTPS status codes show with colors
7. Test add/delete functions
8. Test export CSV

---

## 🎯 KEY FEATURES IMPLEMENTED

✅ 4 stats cards (Total, SSL Valid, Expired Soon, Failed)  
✅ SSL Status History (5 dots with hover tooltips)  
✅ Expiry date with color coding (red < 7 days, green >= 7 days)  
✅ HTTPS status with color coding (green 2xx, yellow 3xx, red 4xx/5xx)  
✅ Advanced filters (SSL status, expiry, HTTPS status)  
✅ Sorting (domain, SSL status, expiry)  
✅ Search functionality  
✅ Bulk operations (add, delete)  
✅ Export to CSV  

---

**Status**: Complete frontend template ready to use!
