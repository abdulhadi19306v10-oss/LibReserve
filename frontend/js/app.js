// Theme Manager
(function() {
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.documentElement.classList.add("light-theme");
    }
})();

document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
    }
    updateThemeIcon();
});

function toggleTheme() {
    const body = document.body;
    body.classList.toggle("light-theme");
    document.documentElement.classList.toggle("light-theme");
    
    const theme = body.classList.contains("light-theme") ? "light" : "dark";
    localStorage.setItem("theme", theme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icons = document.querySelectorAll(".btn-theme-toggle i");
    icons.forEach(icon => {
        if (document.body.classList.contains("light-theme")) {
            icon.className = "fa-solid fa-sun";
        } else {
            icon.className = "fa-solid fa-moon";
        }
    });
}

// LibReserve - Global Application Client Logic

const API_BASE = "/api";

// Returns correct dashboard URL relative to the user role
function getDashboardUrl(role) {
    const roleMap = {
        "Student": "/dashboard/student",
        "Faculty": "/dashboard/faculty",
        "Librarian": "/dashboard/librarian",
        "Library Admin": "/dashboard/lib_admin",
        "System Admin": "/dashboard/sys_admin"
    };
    return roleMap[role] || "/login";
}

// Check session. If not logged in or role mismatch, redirect.
function checkUserSession(requiredRole) {
    const sessionStr = localStorage.getItem("user");
    if (!sessionStr) {
        window.location.href = "/login";
        return null;
    }
    
    const user = JSON.parse(sessionStr);
    if (requiredRole && user.role !== requiredRole) {
        // Mismatch. Forward to their true home.
        window.location.href = getDashboardUrl(user.role);
        return null;
    }
    return user;
}

// Log out user
function logout() {
    localStorage.removeItem("user");
    window.location.href = "/login";
}

// Switch UI tabs on Dashboards
function switchTab(tabName) {
    // Update menu bar active class
    const menuItems = document.querySelectorAll(".sidebar-menu .menu-item");
    menuItems.forEach(item => {
        item.classList.remove("active");
        const link = item.querySelector("a");
        if (link && link.getAttribute("onclick").includes(tabName)) {
            item.classList.add("active");
        }
    });

    // Toggle panels visibility
    const panels = document.querySelectorAll(".tab-content");
    panels.forEach(p => {
        p.style.display = "none";
    });

    const activePanel = document.getElementById(`section-${tabName}`);
    if (activePanel) {
        activePanel.style.display = "block";
    }
}

// Show temporary alert banner in headers
function showAlert(message, type = "success") {
    const zone = document.getElementById("alert-zone");
    if (!zone) return;
    
    const alert = document.createElement("div");
    alert.className = `badge badge-${type}`;
    alert.style.padding = "0.75rem 1.5rem";
    alert.style.borderRadius = "12px";
    alert.style.fontWeight = "600";
    alert.style.fontSize = "0.9rem";
    alert.style.boxShadow = "var(--shadow-soft)";
    alert.style.animation = "fadeIn 0.3s ease-out";
    
    alert.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}" style="margin-right: 0.5rem;"></i>
        <span>${message}</span>
    `;
    
    zone.innerHTML = "";
    zone.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = "fadeOut 0.3s ease-in";
        setTimeout(() => alert.remove(), 300);
    }, 4000);
}

// ==========================================
// LOGIN & REGISTRATION HANDLERS
// ==========================================

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const errorEl = document.getElementById("login-error");
    
    errorEl.style.display = "none";
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed. Try again.");
        }
        
        // Save session user
        localStorage.setItem("user", JSON.stringify(data));
        
        // Redirect
        window.location.href = getDashboardUrl(data.role);
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const firstName = document.getElementById("reg-first-name").value.trim();
    const lastName = document.getElementById("reg-last-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const role = document.getElementById("reg-role").value;
    const id = document.getElementById("reg-id").value.trim();
    const password = document.getElementById("reg-password").value;
    
    const errorEl = document.getElementById("register-error");
    const successEl = document.getElementById("register-success");
    
    errorEl.style.display = "none";
    successEl.style.display = "none";
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id,
                email,
                password,
                first_name: firstName,
                last_name: lastName,
                role
            })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Registration failed. Try again.");
        }
        
        successEl.textContent = `Account created successfully for ${firstName}! Redirecting to Sign In...`;
        successEl.style.display = "block";
        
        // Clear input form
        e.target.reset();
        
        // Switch tab back to login view after short delay
        setTimeout(() => {
            switchAuthTab('login');
            successEl.style.display = "none";
        }, 2500);
        
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}
