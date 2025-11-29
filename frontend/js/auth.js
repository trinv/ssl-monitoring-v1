/**
 * SSL Certificate Monitoring - Authentication Functions
 */

// Storage keys
const STORAGE_KEY_TOKEN = 'ssl_monitor_token';
const STORAGE_KEY_USER = 'ssl_monitor_user';
const STORAGE_KEY_REMEMBER = 'ssl_monitor_remember';

// Get authentication token from storage
function getAuthToken() {
    const remember = localStorage.getItem(STORAGE_KEY_REMEMBER) === 'true';
    const storage = remember ? localStorage : sessionStorage;
    return storage.getItem(STORAGE_KEY_TOKEN);
}

// Set authentication token in storage
function setAuthToken(token, remember = false) {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem(STORAGE_KEY_TOKEN, token);
    localStorage.setItem(STORAGE_KEY_REMEMBER, remember.toString());
}

// Get user info from storage
function getCurrentUser() {
    const remember = localStorage.getItem(STORAGE_KEY_REMEMBER) === 'true';
    const storage = remember ? localStorage : sessionStorage;
    const userJson = storage.getItem(STORAGE_KEY_USER);
    return userJson ? JSON.parse(userJson) : null;
}

// Set user info in storage
function setCurrentUser(user, remember = false) {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
}

// Clear authentication data
function clearAuth() {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
    localStorage.removeItem(STORAGE_KEY_REMEMBER);
    sessionStorage.removeItem(STORAGE_KEY_TOKEN);
    sessionStorage.removeItem(STORAGE_KEY_USER);
}

// Check if user is authenticated
function isAuthenticated() {
    return !!getAuthToken();
}

// Check if user has a specific permission
function hasPermission(permission) {
    const user = getCurrentUser();
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
}

// Check if user has a specific role
function hasRole(roleName) {
    const user = getCurrentUser();
    if (!user) return false;
    return user.role_name === roleName;
}

// Login function
async function login(username, password, remember = false) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            return {
                success: false,
                message: data.detail || 'Login failed'
            };
        }

        // Store token and user info
        setAuthToken(data.token, remember);
        setCurrentUser(data.user, remember);

        return {
            success: true,
            user: data.user,
            token: data.token
        };
    } catch (error) {
        console.error('Login error:', error);
        return {
            success: false,
            message: 'Network error. Please try again.'
        };
    }
}

// Logout function
async function logout() {
    const token = getAuthToken();

    if (token) {
        try {
            // Call logout endpoint
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    // Clear local storage
    clearAuth();

    // Redirect to login page
    window.location.href = 'login.html';
}

// Get current user info from server
async function fetchCurrentUser() {
    const token = getAuthToken();

    if (!token) {
        return null;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid
                clearAuth();
                return null;
            }
            throw new Error('Failed to fetch user info');
        }

        const user = await response.json();

        // Update stored user info
        const remember = localStorage.getItem(STORAGE_KEY_REMEMBER) === 'true';
        setCurrentUser(user, remember);

        return user;
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

// Change password function
async function changePassword(currentPassword, newPassword) {
    const token = getAuthToken();

    if (!token) {
        return {
            success: false,
            message: 'Not authenticated'
        };
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (!response.ok) {
            return {
                success: false,
                message: data.detail || 'Password change failed'
            };
        }

        return {
            success: true,
            message: data.message
        };
    } catch (error) {
        console.error('Change password error:', error);
        return {
            success: false,
            message: 'Network error. Please try again.'
        };
    }
}

// Add authorization header to fetch requests
function authFetch(url, options = {}) {
    const token = getAuthToken();

    if (!token) {
        // Redirect to login if no token
        window.location.href = 'login.html';
        return Promise.reject(new Error('Not authenticated'));
    }

    // Add authorization header
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    return fetch(url, options).then(response => {
        // If unauthorized, redirect to login
        if (response.status === 401) {
            clearAuth();
            window.location.href = 'login.html';
            throw new Error('Session expired');
        }
        return response;
    });
}

// Check authentication on page load (for protected pages)
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Display user info in navbar
function displayUserInfo() {
    const user = getCurrentUser();
    if (!user) return;

    // Update username display
    const usernameElement = document.getElementById('navUsername');
    if (usernameElement) {
        usernameElement.textContent = user.full_name || user.username;
    }

    // Update role badge
    const roleElement = document.getElementById('navUserRole');
    if (roleElement) {
        roleElement.textContent = user.role_name;

        // Apply role-specific badge color
        roleElement.className = 'badge badge-sm';
        if (user.role_name === 'admin') {
            roleElement.classList.add('badge-danger');
        } else if (user.role_name === 'user') {
            roleElement.classList.add('badge-primary');
        } else {
            roleElement.classList.add('badge-secondary');
        }
    }
}

// Initialize authentication for protected pages
function initAuth() {
    // Check if authenticated
    if (!requireAuth()) {
        return false;
    }

    // Display user info
    displayUserInfo();

    // Refresh user info from server
    fetchCurrentUser().catch(err => {
        console.error('Failed to refresh user info:', err);
    });

    return true;
}
