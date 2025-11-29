/**
 * Simple Authentication
 * - Store token in localStorage
 * - Check token on page load
 * - Login/Logout
 */

const STORAGE_KEY_TOKEN = 'ssl_token';
const STORAGE_KEY_USER = 'ssl_user';

// Get token
function getAuthToken() {
    return localStorage.getItem(STORAGE_KEY_TOKEN);
}

// Set token
function setAuthToken(token) {
    localStorage.setItem(STORAGE_KEY_TOKEN, token);
}

// Get user info
function getCurrentUser() {
    const userJson = localStorage.getItem(STORAGE_KEY_USER);
    return userJson ? JSON.parse(userJson) : null;
}

// Set user info
function setCurrentUser(user) {
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
}

// Clear auth
function clearAuth() {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
}

// Check if authenticated
function isAuthenticated() {
    return !!getAuthToken();
}

// Check if admin
function isAdmin() {
    const user = getCurrentUser();
    return user && user.role_name === 'admin';
}

// Login
async function login(username, password) {
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

        // Save token and user
        setAuthToken(data.token);
        setCurrentUser(data.user);

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

// Logout
async function logout() {
    const token = getAuthToken();

    if (token) {
        try {
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

    clearAuth();
    window.location.href = 'login.html';
}

// Get current user from server
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
                clearAuth();
                return null;
            }
            throw new Error('Failed to fetch user info');
        }

        const user = await response.json();
        setCurrentUser(user);
        return user;
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

// Change password
async function changePassword(oldPassword, newPassword) {
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
                old_password: oldPassword,
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

        // Clear auth (user needs to login again)
        clearAuth();

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

// Fetch with auth
function authFetch(url, options = {}) {
    const token = getAuthToken();

    if (!token) {
        window.location.href = 'login.html';
        return Promise.reject(new Error('Not authenticated'));
    }

    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    return fetch(url, options).then(response => {
        if (response.status === 401) {
            clearAuth();
            window.location.href = 'login.html';
            throw new Error('Session expired');
        }
        return response;
    });
}

// Require auth
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Display user info
function displayUserInfo() {
    const user = getCurrentUser();
    if (!user) return;

    // Update username
    const usernameElement = document.getElementById('navUsername');
    if (usernameElement) {
        usernameElement.textContent = user.full_name || user.username;
    }

    // Update role badge
    const roleElement = document.getElementById('navUserRole');
    if (roleElement) {
        roleElement.textContent = user.role_name;
        roleElement.className = 'badge badge-sm';

        if (user.role_name === 'admin') {
            roleElement.classList.add('badge-danger');
        } else {
            roleElement.classList.add('badge-primary');
        }
    }

    // Show/hide admin features
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(el => {
        if (isAdmin()) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
}

// Init auth
function initAuth() {
    if (!requireAuth()) {
        return false;
    }

    displayUserInfo();

    // Refresh user info
    fetchCurrentUser().catch(err => {
        console.error('Failed to refresh user info:', err);
    });

    return true;
}
