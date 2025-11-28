# Frontend Structure - SSL Certificate Monitoring

## 📁 Cấu trúc thư mục mới (Refactored)

```
frontend/
├── index.html              # HTML structure only
├── css/
│   └── style.css          # Custom styles
├── js/
│   ├── config.js          # Configuration & global state
│   ├── api.js             # API calls
│   ├── dashboard.js       # Dashboard functions
│   └── domains.js         # Domain management
└── README.md              # This file
```

## 🔧 Cách sử dụng cấu trúc mới

### Bước 1: Cập nhật `index.html`

Thay thế phần `<style>` trong `<head>` bằng:

```html
<link rel="stylesheet" href="css/style.css">
```

### Bước 2: Thay thế JavaScript

Xóa toàn bộ code JavaScript trong `<script>` tag và thay bằng:

```html
<!-- jQuery & Bootstrap -->
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js"></script>

<!-- Application Scripts -->
<script src="js/config.js"></script>
<script src="js/api.js"></script>
<script src="js/dashboard.js"></script>
<script src="js/domains.js"></script>
```

## 📝 Chi tiết các file

### `css/style.css`
- Info box styles
- Bulk actions styles
- SSL status dot styles
- Expiry badge styles
- Responsive adjustments

### `js/config.js`
- API base URL
- Pagination settings
- Global state variables (currentPage, filters, etc.)
- Constants

### `js/api.js`
- `fetchDashboardSummary()` - Get dashboard data
- `fetchDomains()` - Get domains with pagination/filters
- `createDomain()` - Add single domain
- `createDomainsBulk()` - Add multiple domains
- `deleteDomain()` - Delete single domain
- `deleteDomainsBulk()` - Delete multiple domains
- `triggerFullScan()` - Trigger full SSL scan
- `triggerDomainsScan()` - Trigger selective scan
- `exportCSV()` - Export to CSV

### `js/dashboard.js`
- `loadDashboard()` - Load and display dashboard
- `applyFilter()` - Apply filter from dashboard cards
- `initDashboard()` - Initialize with auto-refresh

### `js/domains.js`
- `loadDomains()` - Load domain list
- `renderDomainTable()` - Render table rows
- `renderPagination()` - Render pagination controls
- `addDomain()` - Add domain dialog
- `bulkDelete()` - Bulk delete operation
- `triggerScan()` - Trigger full scan
- `checkSelectedSSL()` - Check SSL for selected domains
- `checkSingleSSL()` - Check SSL for single domain
- `sortTable()` - Sort table by column
- UI helpers (toggleSelectAll, clearSelection, etc.)

## ✅ Lợi ích của cấu trúc mới

1. **Separation of Concerns**: HTML, CSS, JS tách biệt
2. **Maintainability**: Dễ maintain và debug
3. **Reusability**: Functions có thể reuse
4. **Performance**: Browser cache riêng cho từng file
5. **Team Collaboration**: Nhiều người có thể làm việc đồng thời
6. **Professional**: Chuẩn industry best practices

## 🔄 Migration Guide

Để migrate từ file hiện tại sang cấu trúc mới:

1. Backup file hiện tại:
   ```bash
   cp index.html index.html.backup
   ```

2. Xóa `<style>` block trong `<head>`, thêm link CSS

3. Xóa `<script>` code, thêm link JS files

4. Test kỹ tất cả tính năng

5. Nếu có vấn đề, restore từ backup

## 🎯 Current Status

- ✅ `css/style.css` - Created and updated with all styles
- ✅ `js/config.js` - Created with correct API configuration
- ✅ `js/api.js` - Created with all API functions
- ✅ `js/dashboard.js` - Created with dashboard logic
- ✅ `js/domains.js` - Created with domain management
- ✅ `index.html` - **MIGRATED!** Now uses modular structure

## 📌 Notes

- File backup: `index.html.backup`
- Migration completed successfully!
- Config API_BASE_URL trong `js/config.js` nếu cần thay đổi
- Remember to restart nginx container after changes:
  ```bash
  docker compose restart nginx
  # or
  docker-compose restart nginx
  ```
