# 🔄 MIGRATION TO SSL CERTIFICATE MONITORING

## Project đã được chuyển đổi hoàn toàn từ "Domain For Sale Scanner" → "SSL Certificate Monitor"

---

## ✅ ĐÃ HOÀN THÀNH

### 1. **Database Schema (init.sql)**
- ❌ Removed: scan_results table (for sale status)
- ✅ Added: ssl_scan_results table
  - ssl_status (valid/invalid/no_ssl)
  - ssl_expiry_date
  - days_until_expiry
  - https_status (HTTP status code)
  - redirect_url
  - certificate_issuer
  - certificate_subject
- ✅ Added: Materialized view `latest_ssl_status`
- ✅ Added: Function `get_ssl_status_history()` - trả về 5 lần scan gần nhất
- ✅ Updated: dashboard_summary view với stats mới

### 2. **Scanner (scanner/scanner.py)**
- ✅ Completely rewritten based on check_ssl_bulk.sh
- ✅ Uses Python ssl module để check certificate
- ✅ Uses aiohttp để check HTTPS status
- ✅ Follows redirects (như curl -L)
- ✅ Extracts: SSL status, expiry date, HTTP status, redirect URL
- ✅ Bulk insert với PostgreSQL COPY
- ✅ High concurrency (2000+ domains/second)

### 3. **Backend API (backend/main.py)**
- ✅ New endpoints cho SSL monitoring
- ✅ `/api/dashboard/summary` - Stats: total, valid, expired_soon, failed
- ✅ `/api/domains` - List domains với filters:
  - ssl_status filter
  - expired_soon filter (< 7 days)
  - https_status filter
  - search by domain name
  - sort_by: domain, ssl_status, expiry
- ✅ Returns status_history (5 scans gần nhất)
- ✅ `/api/export/csv` - Export SSL report

---

## 🎨 FRONTEND CẦN TẠO MỚI

### Dashboard Stats (4 cards):

```
┌─────────────────────────────────────────────────┐
│  📊 Total Domains      🟢 SSL Valid             │
│      1,234                 987                  │
│                                                 │
│  ⚠️  Expired Soon      🔴 Failed                │
│      45                    202                  │
└─────────────────────────────────────────────────┘
```

### Domain List Table:

| Domain | SSL Status | Expired on | HTTPS Status | Redirect to | Last Scan | Actions |
|--------|-----------|-----------|-------------|-------------|-----------|---------|
| example.com | 🟢🟢🟢🟢🟢 | 2026-01-15 (51 days) | 200 | - | 2025-11-26 | 🗑️ |
| test.com | 🔴🔴🔴🟢🟢 | 2025-11-30 (4 days) | 301 | https://new.com | 2025-11-26 | 🗑️ |

**Chi tiết từng cột:**

#### 1. SSL Status Column
- Hiển thị 5 dots (status history)
- 🟢 Green = valid
- 🔴 Red = invalid/no_ssl
- Hover để xem chi tiết:
  ```
  Scan 1: Valid (2 days left)
  Scan 2: Valid (9 days left)  
  Scan 3: Valid (16 days left)
  Scan 4: Invalid
  Scan 5: Valid (30 days left)
  ```

#### 2. Expired on Column
- Format: YYYY-MM-DD (X days)
- Màu:
  - 🔴 Red badge: < 7 days
  - 🟢 Green badge: >= 7 days
  - Gray: No SSL/Invalid

#### 3. HTTPS Status Column
- Hiển thị status code: 200, 301, 404, etc.
- Màu:
  - 🟢 Green: 200-299
  - 🟡 Yellow: 300-399
  - 🔴 Red: 400-599, 0 (failed)

#### 4. Redirect to Column
- Hiển thị URL đích (nếu có redirect)
- "-" nếu không có redirect

### Filters & Search:

```
┌─────────────────────────────────────────────────┐
│ Search: [______________] [🔍]                   │
│                                                 │
│ Sort by: [Domain ▼]                            │
│ SSL Status: [All ▼]                            │
│ Expiry: [All ▼]                                │
│ HTTPS Status: [All ▼]                          │
└─────────────────────────────────────────────────┘
```

**Dropdowns:**
- Sort by: Domain (A-Z), SSL Status, Days to Expiry
- SSL Status: All, Valid, Invalid
- Expiry: All, Expired Soon (<7 days), Valid (>7 days)
- HTTPS Status: All, 2xx, 3xx, 4xx, 5xx, Failed

---

## 📝 FRONTEND CODE STRUCTURE

### HTML Structure:
```html
<!-- Stats Cards -->
<div class="row">
  <div class="col-md-3">
    <div class="info-box bg-info">
      <span class="info-box-icon"><i class="fas fa-globe"></i></span>
      <div class="info-box-content">
        <span class="info-box-text">Total Domains</span>
        <span class="info-box-number" id="totalDomains">0</span>
      </div>
    </div>
  </div>
  <!-- Similar for SSL Valid, Expired Soon, Failed -->
</div>

<!-- Filters -->
<div class="card">
  <div class="card-body">
    <div class="row">
      <div class="col-md-3">
        <input type="text" id="searchInput" placeholder="Search domains...">
      </div>
      <div class="col-md-2">
        <select id="sortBy">
          <option value="domain">Domain (A-Z)</option>
          <option value="ssl_status">SSL Status</option>
          <option value="expiry">Days to Expiry</option>
        </select>
      </div>
      <div class="col-md-2">
        <select id="sslStatusFilter">
          <option value="">All</option>
          <option value="valid">Valid</option>
          <option value="invalid">Invalid</option>
        </select>
      </div>
      <div class="col-md-2">
        <select id="expiryFilter">
          <option value="">All</option>
          <option value="expired_soon">Expired Soon</option>
          <option value="valid">Valid</option>
        </select>
      </div>
      <div class="col-md-2">
        <select id="httpsStatusFilter">
          <option value="">All</option>
          <option value="2">2xx Success</option>
          <option value="3">3xx Redirect</option>
          <option value="4">4xx Client Error</option>
          <option value="5">5xx Server Error</option>
          <option value="0">Failed</option>
        </select>
      </div>
    </div>
  </div>
</div>

<!-- Domain Table -->
<table class="table">
  <thead>
    <tr>
      <th><input type="checkbox" id="selectAll"></th>
      <th>Domain</th>
      <th>SSL Status</th>
      <th>Expired on</th>
      <th>HTTPS Status</th>
      <th>Redirect to</th>
      <th>Last Scan</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody id="domainTableBody">
    <!-- Populated by JavaScript -->
  </tbody>
</table>
```

### JavaScript Functions:

```javascript
// Load dashboard
async function loadDashboard() {
  const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
  const data = await response.json();
  
  document.getElementById('totalDomains').textContent = data.total_domains;
  document.getElementById('sslValid').textContent = data.ssl_valid_count;
  document.getElementById('expiredSoon').textContent = data.expired_soon_count;
  document.getElementById('failed').textContent = data.failed_count;
}

// Load domains with filters
async function loadDomains() {
  const sslStatus = document.getElementById('sslStatusFilter').value;
  const expiredSoon = document.getElementById('expiryFilter').value === 'expired_soon';
  const httpsStatus = document.getElementById('httpsStatusFilter').value;
  const search = document.getElementById('searchInput').value;
  const sortBy = document.getElementById('sortBy').value;
  
  let url = `${API_BASE_URL}/domains?limit=100&sort_by=${sortBy}`;
  if (sslStatus) url += `&ssl_status=${sslStatus}`;
  if (expiredSoon) url += `&expired_soon=true`;
  if (httpsStatus) url += `&https_status=${httpsStatus}`;
  if (search) url += `&search=${search}`;
  
  const response = await fetch(url);
  const domains = await response.json();
  
  renderDomainTable(domains);
}

// Render domain table
function renderDomainTable(domains) {
  const tbody = document.getElementById('domainTableBody');
  tbody.innerHTML = domains.map(d => `
    <tr>
      <td><input type="checkbox" value="${d.id}"></td>
      <td>${d.domain}</td>
      <td>${renderSSLStatusDots(d.status_history)}</td>
      <td>${renderExpiryDate(d.ssl_expiry_date, d.days_until_expiry)}</td>
      <td>${renderHTTPSStatus(d.https_status)}</td>
      <td>${d.redirect_url || '-'}</td>
      <td>${formatDate(d.scan_time)}</td>
      <td>
        <button onclick="deleteDomain(${d.id})" class="btn btn-sm btn-danger">
          <i class="fas fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

// Render SSL status dots with history
function renderSSLStatusDots(history) {
  if (!history || history.length === 0) {
    return '<span class="text-muted">No data</span>';
  }
  
  return history.slice(0, 5).map(h => {
    const color = h.ssl_status === 'valid' ? 'success' : 'danger';
    const tooltip = `${h.ssl_status} - ${h.days_until_expiry || 'N/A'} days - ${formatDate(h.scan_time)}`;
    
    return `<span class="badge badge-dot badge-${color}" 
                  data-toggle="tooltip" 
                  title="${tooltip}">●</span>`;
  }).join(' ');
}

// Render expiry date with color
function renderExpiryDate(expiryDate, daysUntil) {
  if (!expiryDate) {
    return '<span class="badge badge-secondary">N/A</span>';
  }
  
  const badgeClass = daysUntil < 7 ? 'badge-danger' : 'badge-success';
  const dateStr = new Date(expiryDate).toISOString().split('T')[0];
  
  return `<span class="badge ${badgeClass}">${dateStr} (${daysUntil} days)</span>`;
}

// Render HTTPS status code
function renderHTTPSStatus(status) {
  if (!status || status === 0) {
    return '<span class="badge badge-danger">Failed</span>';
  }
  
  let badgeClass = 'badge-secondary';
  if (status >= 200 && status < 300) badgeClass = 'badge-success';
  else if (status >= 300 && status < 400) badgeClass = 'badge-warning';
  else if (status >= 400) badgeClass = 'badge-danger';
  
  return `<span class="badge ${badgeClass}">${status}</span>`;
}
```

---

## 🚀 DEPLOYMENT

### 1. Stop current system:
```bash
cd domain-monitor
docker-compose down -v
```

### 2. Extract new version:
```bash
tar -xzf domain-monitor-v2.0.tar.gz
cd domain-monitor
```

### 3. Start new system:
```bash
docker-compose up -d --build
```

### 4. Verify:
```bash
# Check services
docker-compose ps

# Check database
docker-compose exec postgres psql -U domainuser -d domains -c "\dt"

# Check API
curl http://YOUR_IP_ADDRESS:8080/api/dashboard/summary
```

---

## 📊 API ENDPOINTS SUMMARY

### GET /api/dashboard/summary
Returns:
```json
{
  "total_domains": 1234,
  "ssl_valid_count": 987,
  "expired_soon_count": 45,
  "failed_count": 202,
  "last_scan_time": "2025-11-26T10:00:00"
}
```

### GET /api/domains
Query params:
- `ssl_status`: valid/invalid/no_ssl
- `expired_soon`: true/false
- `https_status`: 200, 301, 404, etc.
- `search`: domain name
- `sort_by`: domain/ssl_status/expiry
- `limit`: 100 (default)
- `offset`: 0

Returns:
```json
[
  {
    "id": 1,
    "domain": "example.com",
    "ssl_status": "valid",
    "ssl_expiry_date": "2026-01-15T00:00:00",
    "days_until_expiry": 51,
    "https_status": 200,
    "redirect_url": null,
    "error_type": null,
    "scan_time": "2025-11-26T10:00:00",
    "status_history": [
      {
        "scan_time": "2025-11-26T10:00:00",
        "ssl_status": "valid",
        "days_until_expiry": 51,
        "https_status": 200
      },
      // ... 4 more recent scans
    ]
  }
]
```

---

## ✅ TESTING CHECKLIST

- [ ] Database schema created correctly
- [ ] Scanner can check SSL certificates
- [ ] Scanner can check HTTPS status
- [ ] Scanner saves results to database
- [ ] API returns dashboard summary
- [ ] API returns domain list with filters
- [ ] API returns status history
- [ ] Frontend displays 4 stats cards
- [ ] Frontend displays domain table
- [ ] Frontend shows SSL status dots (5 history)
- [ ] Frontend shows expiry date with colors
- [ ] Frontend shows HTTPS status with colors
- [ ] Frontend filters work (SSL status, expiry, HTTPS)
- [ ] Frontend search works
- [ ] Frontend sorting works
- [ ] Add domain works
- [ ] Bulk add works
- [ ] Delete domain works
- [ ] Export CSV works

---

## 🎉 READY!

New SSL Certificate Monitoring system is ready to deploy!

**Version**: 2.0.0  
**Type**: SSL Certificate Monitor  
**Features**: 
- SSL certificate validation
- Expiry date tracking
- HTTPS status checking
- Redirect detection
- Historical tracking (5 scans)
- Advanced filtering & sorting
