/**
 * SSL Certificate Monitoring - Configuration
 */

// API Configuration
const API_BASE_URL = 'http://74.48.129.112:8080/api';

// Pagination Settings
const ITEMS_PER_PAGE = 100;

// Auto-refresh Intervals (milliseconds)
const DASHBOARD_REFRESH_INTERVAL = 30000; // 30 seconds
const SCAN_COMPLETION_WAIT = 10000; // 10 seconds after triggering scan

// Filter Options
const SSL_STATUS_OPTIONS = {
    ALL: null,
    VALID: 'VALID',
    INVALID: 'INVALID'
};

// Global State
let currentPage = 1;
let totalPages = 1;
let totalDomains = 0;
let currentSortBy = 'domain';
let currentSortOrder = 'asc';
let currentFilters = {
    sslStatus: null,
    expiredSoon: false,
    search: ''
};
