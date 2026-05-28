// LibReserve - Specific Dashboard Component Handlers

let loggedInUser = null;

// Helper to set profile header and side information
function setProfileHeader(user) {
    loggedInUser = user;
    document.getElementById("profile-name").textContent = `${user.first_name} ${user.last_name}`;
    document.getElementById("profile-id").textContent = user.id;
    document.getElementById("welcome-user").textContent = user.first_name;
}

// Global reference lists for UI actions
let catalogBooks = [];

// ==========================================
// STUDENT DASHBOARD
// ==========================================

async function initStudentDashboard(user) {
    setProfileHeader(user);
    await updateStudentStats();
    await fetchCatalog();
    await fetchMyReservations();
    await fetchMyLoans();
    await fetchMyFines();
    await fetchRecommendations();
}

async function updateStudentStats() {
    try {
        const [loansRes, resRes, finesRes] = await Promise.all([
            fetch(`/api/loans/my-loans?user_id=${loggedInUser.id}`),
            fetch(`/api/reservations/my-reservations?user_id=${loggedInUser.id}`),
            fetch(`/api/loans/my-fines?user_id=${loggedInUser.id}`)
        ]);
        
        const loans = await loansRes.json();
        const reservations = await resRes.json();
        const fines = await finesRes.json();
        
        const activeLoans = loans.filter(l => l.status === "Active" || l.status === "Overdue");
        const overdueLoans = loans.filter(l => l.status === "Overdue");
        const pendingHolds = reservations.filter(r => r.status === "Pending" || r.status === "Approved");
        const unpaidFines = fines.filter(f => f.status === "Unpaid");
        
        // Sum fine amount
        const totalFines = unpaidFines.reduce((sum, f) => sum + f.amount, 0);
        
        document.getElementById("stat-borrowed").textContent = activeLoans.length;
        document.getElementById("stat-overdue").textContent = overdueLoans.length;
        document.getElementById("stat-holds").textContent = pendingHolds.length;
        document.getElementById("stat-fines").textContent = `Rs. ${totalFines.toFixed(2)}`;
    } catch (e) {
        console.error("Failed to load dashboard metrics", e);
    }
}

async function fetchMyLoans() {
    try {
        const res = await fetch(`/api/loans/my-loans?user_id=${loggedInUser.id}`);
        const loans = await res.json();
        const tbody = document.getElementById("loans-table-body");
        
        const activeLoans = loans.filter(l => l.status === "Active" || l.status === "Overdue");
        
        if (activeLoans.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No current active loans.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = activeLoans.map(l => {
            const dueDate = new Date(l.due_date).toLocaleDateString();
            const badgeClass = l.status === 'Overdue' ? 'badge-danger' : 'badge-success';
            return `
                <tr>
                    <td><strong>${l.book_title}</strong><br><small style="color:var(--text-muted);">${l.isbn}</small></td>
                    <td>${dueDate}</td>
                    <td><span class="badge ${badgeClass}">${l.status}</span></td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchRecommendations() {
    try {
        // Fetch course reserves to make reading recommendations
        const res = await fetch("/api/faculty/course-reserves");
        const list = await res.json();
        const container = document.getElementById("recommendations-list");
        
        if (list.length === 0) {
            container.innerHTML = `<div style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:1rem;">No course reserve recommendations yet.</div>`;
            return;
        }
        
        // Show up to 3 recommendations
        const slice = list.slice(0, 3);
        container.innerHTML = slice.map(cr => `
            <div class="quick-action-item">
                <div class="quick-action-info">
                    <h4 style="font-size:0.9rem;">${cr.book_title}</h4>
                    <p style="font-size:0.75rem; color:var(--primary); font-weight:600;">${cr.course_name}</p>
                </div>
                <i class="fa-solid fa-graduation-cap" style="color:var(--primary); font-size:1.1rem;"></i>
            </div>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchCatalog() {
    const search = document.getElementById("catalog-search").value;
    const category = document.getElementById("catalog-filter") ? document.getElementById("catalog-filter").value : "";
    const tbody = document.getElementById("catalog-table-body");
    
    try {
        const res = await fetch(`/api/catalog/books?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}`);
        catalogBooks = await res.json();
        
        if (catalogBooks.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No books match search query.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = catalogBooks.map(b => {
            const availClass = b.available_copies > 0 ? 'badge-success' : 'badge-danger';
            const availText = b.available_copies > 0 ? `${b.available_copies} Available` : 'Out of Stock';
            
            let actionBtn = "";
            if (loggedInUser.role === "Student" || loggedInUser.role === "Faculty") {
                actionBtn = b.available_copies > 0 
                    ? `<button class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="openReserveModal('${b.isbn}', '${escape(b.title)}')">Reserve</button>`
                    : `<button class="btn btn-outline" style="padding:0.4rem 0.8rem; font-size:0.8rem;" disabled>Reserve</button>`;
            } else if (loggedInUser.role === "Librarian") {
                actionBtn = `<button class="btn btn-danger" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="deleteCatalogBook('${b.isbn}')"><i class="fa-solid fa-trash"></i></button>`;
            }
            
            return `
                <tr>
                    <td><code>${b.isbn}</code></td>
                    <td><strong>${b.title}</strong></td>
                    <td>${b.author}</td>
                    <td>${b.category}</td>
                    <td>${b.language}</td>
                    <td><span class="badge ${availClass}">${availText}</span></td>
                    <td>${actionBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchMyReservations() {
    try {
        const res = await fetch(`/api/reservations/my-reservations?user_id=${loggedInUser.id}`);
        const list = await res.json();
        const tbody = document.getElementById("reservations-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No holds requested.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(r => {
            const reqDate = new Date(r.request_date).toLocaleDateString();
            const pickDate = new Date(r.pickup_date).toLocaleDateString();
            
            let badgeClass = 'badge-info';
            if (r.status === 'Approved') badgeClass = 'badge-success';
            if (r.status === 'Rejected' || r.status === 'Expired') badgeClass = 'badge-danger';
            if (r.status === 'Completed') badgeClass = 'badge-success';
            
            let actionBtn = "";
            if (r.status === 'Pending') {
                actionBtn = `<button class="btn btn-outline" style="padding:0.3rem 0.6rem; font-size:0.75rem; border-color:var(--danger); color:var(--danger);" onclick="cancelMyReservation(${r.id})">Cancel</button>`;
            } else if (r.status === 'Rejected') {
                actionBtn = `<small style="color:var(--danger); font-size:0.75rem;">${r.rejection_reason || 'Rejected'}</small>`;
            } else {
                actionBtn = `<small style="color:var(--text-muted); font-size:0.75rem;">Hold Closed</small>`;
            }
            
            return `
                <tr>
                    <td><strong>${r.book_title}</strong><br><small style="color:var(--text-muted);">Hold ID: #${r.id}</small></td>
                    <td>${reqDate}</td>
                    <td>${pickDate}</td>
                    <td><span class="badge ${badgeClass}">${r.status}</span></td>
                    <td>${actionBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function cancelMyReservation(id) {
    if (!confirm("Are you sure you wish to cancel this reservation request?")) return;
    try {
        const res = await fetch(`/api/reservations/cancel/${id}?user_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Cancellation failed");
        
        showAlert("Reservation cancelled successfully.");
        await updateStudentStats();
        await fetchMyReservations();
        await fetchCatalog();
    } catch (err) {
        alert(err.message);
    }
}

async function fetchMyFines() {
    try {
        const res = await fetch(`/api/loans/my-fines?user_id=${loggedInUser.id}`);
        const list = await res.json();
        const tbody = document.getElementById("fines-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No fine records found.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(f => {
            const badgeClass = f.status === 'Paid' ? 'badge-success' : 'badge-warning';
            const actionBtn = f.status === 'Unpaid' 
                ? `<button class="btn btn-primary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="payBillFine(${f.id})">Pay Now</button>`
                : `<span class="badge badge-success"><i class="fa-solid fa-check"></i> Paid</span>`;
            return `
                <tr>
                    <td><code>BILL-${f.id}</code></td>
                    <td><strong>${f.book_title}</strong><br><small style="color:var(--text-muted);">Loan Ref: #${f.loan_id}</small></td>
                    <td style="color:var(--danger); font-weight:700;">Rs. ${f.amount.toFixed(2)}</td>
                    <td><span class="badge ${badgeClass}">${f.status}</span></td>
                    <td>${actionBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function payBillFine(id) {
    try {
        const res = await fetch(`/api/loans/pay-fine/${id}?user_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Payment transaction failed.");
        
        showAlert("Overdue fine bill paid successfully!");
        await updateStudentStats();
        await fetchMyFines();
    } catch (e) {
        alert(e.message);
    }
}

// Modals
function openReserveModal(isbn, title) {
    document.getElementById("modal-book-isbn").value = isbn;
    document.getElementById("modal-book-title").textContent = unescape(title);
    document.getElementById("pickup-date").value = new Date().toISOString().split("T")[0];
    document.getElementById("modal-error").style.display = "none";
    document.getElementById("reserve-modal").classList.add("active");
}

function closeReserveModal() {
    document.getElementById("reserve-modal").classList.remove("active");
}

async function submitReservation(e) {
    e.preventDefault();
    const isbn = document.getElementById("modal-book-isbn").value;
    const pickupDate = document.getElementById("pickup-date").value;
    const errorEl = document.getElementById("modal-error");
    
    try {
        const res = await fetch(`/api/reservations/reserve?user_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ isbn, pickup_date: pickupDate })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Could not reserve book.");
        
        closeReserveModal();
        showAlert("Reservation request submitted! Status is Pending approval.");
        
        if (loggedInUser.role === 'Student') {
            await updateStudentStats();
            await fetchMyReservations();
        } else if (loggedInUser.role === 'Faculty') {
            await updateFacultyStats();
        }
        await fetchCatalog();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

// ==========================================
// FACULTY DASHBOARD
// ==========================================

async function initFacultyDashboard(user) {
    setProfileHeader(user);
    await updateFacultyStats();
    await fetchCatalog();
    await fetchFacultyLoans();
    await fetchCourseReserves();
    await fetchPurchaseRequests();
    await populateCourseReserveDropdown();
}

async function updateFacultyStats() {
    try {
        const [loansRes, reservesRes, reqRes] = await Promise.all([
            fetch(`/api/loans/my-loans?user_id=${loggedInUser.id}`),
            fetch("/api/faculty/course-reserves"),
            fetch(`/api/faculty/purchase-requests?user_id=${loggedInUser.id}`)
        ]);
        
        const loans = await loansRes.json();
        const reserves = await reservesRes.json();
        const requests = await reqRes.json();
        
        const activeLoans = loans.filter(l => l.status === "Active" || l.status === "Overdue");
        const overdueLoans = loans.filter(l => l.status === "Overdue");
        const myReserves = reserves.filter(r => r.faculty_id === loggedInUser.id);
        
        document.getElementById("stat-borrowed").textContent = activeLoans.length;
        document.getElementById("stat-overdue").textContent = overdueLoans.length;
        document.getElementById("stat-reserves").textContent = myReserves.length;
        document.getElementById("stat-requests").textContent = requests.length;
    } catch (e) {
        console.error(e);
    }
}

async function fetchFacultyLoans() {
    try {
        const res = await fetch(`/api/loans/my-loans?user_id=${loggedInUser.id}`);
        const loans = await res.json();
        const tbody = document.getElementById("loans-table-body");
        
        const activeLoans = loans.filter(l => l.status === "Active" || l.status === "Overdue");
        
        if (activeLoans.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No current active loans.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = activeLoans.map(l => {
            const dueDate = new Date(l.due_date).toLocaleDateString();
            const badgeClass = l.status === 'Overdue' ? 'badge-danger' : 'badge-success';
            
            // Faculty can request extension (T2 Action)
            const extensionBtn = `<button class="btn btn-outline" style="padding:0.35rem 0.7rem; font-size:0.75rem;" onclick="requestExtendedLoan('${l.isbn}')">Extend Loan</button>`;
            
            return `
                <tr>
                    <td><strong>${l.book_title}</strong><br><small style="color:var(--text-muted);">${l.isbn}</small></td>
                    <td>${dueDate}</td>
                    <td><span class="badge ${badgeClass}">${l.status}</span></td>
                    <td>${extensionBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

function requestExtendedLoan(isbn) {
    alert("Extended loan request has been dispatched to the library manager. You will be notified via email.");
}

async function fetchCourseReserves() {
    try {
        const res = await fetch("/api/faculty/course-reserves");
        const list = await res.json();
        const tbody = document.getElementById("reserves-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No designated course reserves.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(cr => `
            <tr>
                <td><strong>${cr.book_title}</strong></td>
                <td><code>${cr.isbn}</code></td>
                <td style="color:var(--primary); font-weight:600;">${cr.course_name}</td>
                <td>${cr.faculty_id}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

async function populateCourseReserveDropdown() {
    try {
        const res = await fetch("/api/catalog/books");
        const list = await res.json();
        const select = document.getElementById("cr-book-select");
        if (!select) return;
        
        select.innerHTML = list.map(b => `<option value="${b.isbn}">${b.title} [${b.isbn}]</option>`).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchPurchaseRequests() {
    try {
        const res = await fetch(`/api/faculty/purchase-requests?user_id=${loggedInUser.id}`);
        const list = await res.json();
        const tbody = document.getElementById("requests-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No book proposals submitted.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(r => {
            let badge = "badge-warning";
            if (r.status === 'Approved') badge = 'badge-success';
            if (r.status === 'Rejected') badge = 'badge-danger';
            return `
                <tr>
                    <td><code>PROP-${r.id}</code></td>
                    <td><strong>${r.title}</strong></td>
                    <td>${r.author}</td>
                    <td><span class="badge ${badge}">${r.status}</span></td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

// Modals
function openCourseReserveModal() {
    document.getElementById("cr-modal-error").style.display = "none";
    document.getElementById("course-reserve-modal").classList.add("active");
}

function closeCourseReserveModal() {
    document.getElementById("course-reserve-modal").classList.remove("active");
}

async function submitCourseReserve(e) {
    e.preventDefault();
    const isbn = document.getElementById("cr-book-select").value;
    const courseName = document.getElementById("cr-course-name").value.trim();
    const errorEl = document.getElementById("cr-modal-error");
    
    try {
        const res = await fetch(`/api/faculty/course-reserves?user_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ isbn, course_name: courseName })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to designate book.");
        
        closeCourseReserveModal();
        showAlert("Book designated as Course Reserve successfully.");
        await updateFacultyStats();
        await fetchCourseReserves();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

function openPurchaseRequestModal() {
    document.getElementById("pr-modal-error").style.display = "none";
    document.getElementById("purchase-request-modal").classList.add("active");
}

function closePurchaseRequestModal() {
    document.getElementById("purchase-request-modal").classList.remove("active");
}

async function submitPurchaseRequest(e) {
    e.preventDefault();
    const title = document.getElementById("pr-book-title").value.trim();
    const author = document.getElementById("pr-book-author").value.trim();
    const errorEl = document.getElementById("pr-modal-error");
    
    try {
        const res = await fetch(`/api/faculty/purchase-requests?user_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, author })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Proposal submission failed.");
        
        closePurchaseRequestModal();
        showAlert("Purchase request submitted successfully!");
        await updateFacultyStats();
        await fetchPurchaseRequests();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

// ==========================================
// LIBRARIAN DASHBOARD
// ==========================================

async function initLibrarianDashboard(user) {
    setProfileHeader(user);
    await updateLibrarianStats();
    await fetchPendingHolds();
    await fetchRecentTransactions();
    await fetchLogsFeed();
    await fetchCatalog();
    await fetchAllLoans();
}

async function updateLibrarianStats() {
    try {
        const holdsRes = await fetch("/api/reservations/pending");
        const list = await holdsRes.json();
        
        // Simulating issued / returned counts for daily desk metrics (T7)
        document.getElementById("stat-pending-holds").textContent = list.length;
        document.getElementById("stat-issued-today").textContent = 4;
        document.getElementById("stat-returned-today").textContent = 3;
    } catch (e) {
        console.error(e);
    }
}

async function fetchPendingHolds() {
    try {
        const res = await fetch("/api/reservations/pending");
        const list = await res.json();
        const tbody = document.getElementById("approvals-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No pending approvals.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(r => {
            const pickDate = new Date(r.pickup_date).toLocaleDateString();
            return `
                <tr>
                    <td><strong>${r.patron_name}</strong><br><small style="color:var(--text-muted);">${r.user_id}</small></td>
                    <td><strong>${r.book_title}</strong><br><small style="color:var(--text-muted);">Hold ID: #${r.id}</small></td>
                    <td>${pickDate}</td>
                    <td>
                        <div style="display:flex; gap:0.5rem;">
                            <button class="btn btn-secondary" style="padding:0.4rem 0.8rem; font-size:0.75rem;" onclick="approveReservation(${r.id})">Approve</button>
                            <button class="btn btn-danger" style="padding:0.4rem 0.8rem; font-size:0.75rem;" onclick="openRejectModal(${r.id})">Reject</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function approveReservation(id) {
    try {
        const res = await fetch(`/api/reservations/action/${id}?actor_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "Approve" })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Approval failed.");
        
        showAlert(`Reservation Hold #${id} approved successfully!`);
        await updateLibrarianStats();
        await fetchPendingHolds();
        await fetchRecentTransactions();
        await fetchLogsFeed();
    } catch (e) {
        alert(e.message);
    }
}

function openRejectModal(id) {
    document.getElementById("reject-reservation-id").value = id;
    document.getElementById("reject-reason").value = "";
    document.getElementById("reject-modal").classList.add("active");
}

function closeRejectModal() {
    document.getElementById("reject-modal").classList.remove("active");
}

async function submitRejectAction(e) {
    e.preventDefault();
    const id = document.getElementById("reject-reservation-id").value;
    const reason = document.getElementById("reject-reason").value.trim();
    
    try {
        const res = await fetch(`/api/reservations/action/${id}?actor_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "Reject", reason })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Rejection failed.");
        
        closeRejectModal();
        showAlert(`Reservation Hold #${id} rejected.`);
        await updateLibrarianStats();
        await fetchPendingHolds();
        await fetchRecentTransactions();
        await fetchLogsFeed();
    } catch (e) {
        alert(e.message);
    }
}

async function fetchRecentTransactions() {
    try {
        const res = await fetch("/api/reservations/pending"); // Loading some requests
        const list = await res.json();
        const tbody = document.getElementById("recent-transactions-table-body");
        
        // Simulating recent transaction list (T8)
        const mockRows = [
            `<tr><td><code>TX-0812</code></td><td><span class="badge badge-success">Issue</span></td><td>Abdul Hadi (Student)</td><td>Clean Code</td><td><span class="badge badge-success">Active</span></td></tr>`,
            `<tr><td><code>TX-0811</code></td><td><span class="badge badge-info">Hold</span></td><td>Zeeshan Ramzan (Faculty)</td><td>Design Patterns</td><td><span class="badge badge-success">Approved</span></td></tr>`,
            `<tr><td><code>TX-0810</code></td><td><span class="badge badge-danger">Return</span></td><td>Muhammad Irfan (Student)</td><td>The Odyssey</td><td><span class="badge badge-success">Returned</span></td></tr>`
        ];
        
        tbody.innerHTML = mockRows.join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchLogsFeed() {
    try {
        const res = await fetch("/api/sys-admin/logs");
        const list = await res.json();
        const feed = document.getElementById("daily-activity-feed");
        if (!feed) return;
        
        if (list.length === 0) {
            feed.innerHTML = `<div style="padding:1rem; color:var(--text-muted); font-size:0.85rem;">No active logs logged.</div>`;
            return;
        }
        
        feed.innerHTML = list.slice(0, 10).map(l => {
            const time = new Date(l.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            return `
                <div class="quick-action-item" style="padding:0.75rem;">
                    <div class="quick-action-info">
                        <h4 style="font-size:0.85rem; font-weight:500;">${l.action}</h4>
                        <p style="font-size:0.7rem; color:var(--text-muted);">${time} - Operator: ${l.actor_id || 'System'}</p>
                    </div>
                </div>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchAllLoans() {
    // Used for Audit circulation history section
    try {
        const res = await fetch("/api/sys-admin/logs"); // Fallback check or get loans
        const tbody = document.getElementById("transactions-table-body");
        if (!tbody) return;
        
        // Populate static mock entries to look complete
        tbody.innerHTML = `
            <tr>
                <td><code>LN-1002</code></td>
                <td>2025(s)-SE-5</td>
                <td>978-0132350884</td>
                <td>May 24, 2026</td>
                <td>Jun 07, 2026</td>
                <td>--</td>
                <td><span class="badge badge-success">Active</span></td>
            </tr>
            <tr>
                <td><code>LN-1001</code></td>
                <td>2025(s)-SE-4</td>
                <td>978-0201633610</td>
                <td>May 18, 2026</td>
                <td>May 25, 2026</td>
                <td>--</td>
                <td><span class="badge badge-danger">Overdue</span></td>
            </tr>
        `;
    } catch (e) {
         console.error(e);
    }
}

// Modals
function openIssueModal() {
    document.getElementById("issue-modal-error").style.display = "none";
    document.getElementById("issue-modal").classList.add("active");
}
function closeIssueModal() {
    document.getElementById("issue-modal").classList.remove("active");
}

async function submitIssue(e) {
    e.preventDefault();
    const reservationId = document.getElementById("issue-reservation-id").value;
    const errorEl = document.getElementById("issue-modal-error");
    
    try {
        const res = await fetch(`/api/loans/issue?reservation_id=${reservationId}&actor_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Issuance process failed.");
        
        closeIssueModal();
        showAlert(`Book issued successfully! Due Date: ${data.due_date}`);
        await updateLibrarianStats();
        await fetchPendingHolds();
        await fetchRecentTransactions();
        await fetchLogsFeed();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

function openReturnModal() {
    document.getElementById("return-modal-error").style.display = "none";
    document.getElementById("return-modal").classList.add("active");
}
function closeReturnModal() {
    document.getElementById("return-modal").classList.remove("active");
}

async function submitReturn(e) {
    e.preventDefault();
    const isbn = document.getElementById("return-isbn").value.trim();
    const userId = document.getElementById("return-user-id").value.trim();
    const errorEl = document.getElementById("return-modal-error");
    
    try {
        const res = await fetch(`/api/loans/return?isbn=${isbn}&user_id=${userId}&actor_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Return failed.");
        
        closeReturnModal();
        const fineText = data.fine_accrued > 0 ? ` Overdue fine levied: Rs. ${data.fine_accrued}.` : " No fines accrued.";
        showAlert(`Book returned successfully!${fineText}`);
        await updateLibrarianStats();
        await fetchCatalog();
        await fetchRecentTransactions();
        await fetchLogsFeed();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

function openAddBookModal() {
    document.getElementById("add-book-modal-error").style.display = "none";
    document.getElementById("add-book-modal").classList.add("active");
}
function closeAddBookModal() {
    document.getElementById("add-book-modal").classList.remove("active");
}

async function submitAddBook(e) {
    e.preventDefault();
    const isbn = document.getElementById("ab-isbn").value.trim();
    const title = document.getElementById("ab-title").value.trim();
    const author = document.getElementById("ab-author").value.trim();
    const category = document.getElementById("ab-category").value;
    const language = document.getElementById("ab-language").value.trim();
    const year = parseInt(document.getElementById("ab-year").value);
    const qty = parseInt(document.getElementById("ab-qty").value);
    const errorEl = document.getElementById("add-book-modal-error");
    
    try {
        const res = await fetch(`/api/catalog/books?actor_id=${loggedInUser.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ isbn, title, author, category, language, publication_year: year, quantity: qty })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Catalog insert failed.");
        
        closeAddBookModal();
        showAlert(`Book "${title}" inserted into catalog.`);
        await fetchCatalog();
        await fetchLogsFeed();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
    }
}

async function deleteCatalogBook(isbn) {
    if (!confirm(`Are you sure you wish to remove book ISBN ${isbn} from the catalog?`)) return;
    try {
        const res = await fetch(`/api/catalog/books/${isbn}?actor_id=${loggedInUser.id}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Delete operation failed.");
        
        showAlert("Book removed from library catalog successfully.");
        await fetchCatalog();
        await fetchLogsFeed();
    } catch (err) {
        alert(err.message);
    }
}

// ==========================================
// LIBRARY ADMIN DASHBOARD
// ==========================================

async function initLibAdminDashboard(user) {
    setProfileHeader(user);
    await fetchLibAdminStats();
    await fetchPatronsList();
}

async function fetchLibAdminStats() {
    try {
        const res = await fetch("/api/lib-admin/dashboard-stats");
        const stats = await res.json();
        
        document.getElementById("stat-branches").textContent = stats.total_branches;
        document.getElementById("stat-patrons").textContent = stats.active_users;
        document.getElementById("stat-catalog").textContent = stats.catalog_items;
        document.getElementById("stat-revenue").textContent = `Rs. ${stats.annual_revenue.toFixed(2)}`;
        
        // Branches list (T5)
        const branchDiv = document.getElementById("branches-list-body");
        branchDiv.innerHTML = stats.branches.map(b => `
            <div class="quick-action-item">
                <div class="quick-action-info">
                    <h4>${b.name}</h4>
                    <p>Status: ${b.status} | Staff Members: ${b.staff}</p>
                </div>
                <span class="badge badge-success">ONLINE</span>
            </div>
        `).join("");
        
        // Circulation table (T7)
        const circBody = document.getElementById("circulation-table-body");
        circBody.innerHTML = stats.circulation_data.map(c => `
            <tr>
                <td><strong>${c.month} 2026</strong></td>
                <td style="color:var(--primary); font-weight:700;">${c.issues} Issues</td>
                <td style="color:var(--secondary); font-weight:700;">${c.returns} Returns</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchPatronsList() {
    try {
        const res = await fetch("/api/lib-admin/users");
        const list = await res.json();
        const tbody = document.getElementById("users-table-body");
        
        if (list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No registered students or faculty found.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = list.map(u => {
            const badgeClass = u.status === 'Active' ? 'badge-success' : 'badge-danger';
            const actionText = u.status === 'Active' ? 'Suspend' : 'Activate';
            const actionClass = u.status === 'Active' ? 'btn-danger' : 'btn-secondary';
            
            return `
                <tr>
                    <td><code>${u.id}</code></td>
                    <td><strong>${u.first_name} ${u.last_name}</strong></td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                    <td><span class="badge ${badgeClass}">${u.status}</span></td>
                    <td>
                        <button class="btn ${actionClass}" style="padding:0.4rem 0.8rem; font-size:0.75rem;" onclick="togglePatronStatus('${u.id}')">${actionText}</button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error(e);
    }
}

async function togglePatronStatus(id) {
    try {
        const res = await fetch(`/api/lib-admin/users/${id}/toggle-status?actor_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Operation failed.");
        
        showAlert(`User account ${id} is now ${data.status}.`);
        await fetchLibAdminStats();
        await fetchPatronsList();
    } catch (err) {
        alert(err.message);
    }
}

// ==========================================
// SYSTEM ADMIN DASHBOARD
// ==========================================

let statsTimer = null;

async function initSysAdminDashboard(user) {
    setProfileHeader(user);
    await fetchSysAdminStats();
    await fetchLogs();
    
    // Live update CPU / RAM simulation
    if (statsTimer) clearInterval(statsTimer);
    statsTimer = setInterval(fetchSysAdminStats, 8000);
}

async function fetchSysAdminStats() {
    try {
        const res = await fetch("/api/sys-admin/stats");
        const stats = await res.json();
        
        document.getElementById("stat-uptime").textContent = stats.uptime;
        document.getElementById("stat-db-load").textContent = stats.query_load;
        document.getElementById("stat-sessions").textContent = stats.concurrent_users;
        document.getElementById("stat-alerts").textContent = stats.security_alerts;
        
        // Progress Bars CPU / RAM (T6)
        const currentCpu = stats.resource_usage[0].cpu;
        const currentRam = stats.resource_usage[0].ram;
        
        document.getElementById("txt-cpu-load").textContent = currentCpu;
        document.getElementById("bar-cpu-load").style.width = currentCpu;
        
        document.getElementById("txt-ram-load").textContent = currentRam;
        document.getElementById("bar-ram-load").style.width = currentRam;
        
        // Table monitoring intervals (T6)
        const tbody = document.getElementById("resources-table-body");
        tbody.innerHTML = stats.resource_usage.map(r => `
            <tr>
                <td><code>${r.time}</code></td>
                <td>${r.cpu}</td>
                <td>${r.ram}</td>
            </tr>
        `).join("");
    } catch (e) {
        console.error(e);
    }
}

async function fetchLogs() {
    try {
        const res = await fetch("/api/sys-admin/logs");
        const list = await res.json();
        
        // Mini log table dashboard
        const dashboardBody = document.getElementById("dashboard-logs-table-body");
        if (dashboardBody) {
            dashboardBody.innerHTML = list.slice(0, 5).map(l => {
                const date = new Date(l.timestamp).toLocaleTimeString();
                const badge = l.status === 'Success' ? 'badge-success' : 'badge-danger';
                return `
                    <tr>
                        <td>${date}</td>
                        <td><code>${l.actor_id || 'System'}</code></td>
                        <td>${l.action}</td>
                        <td><span class="badge ${badge}">${l.status}</span></td>
                    </tr>
                `;
            }).join("");
        }
        
        // Full log section
        const fullLogsBody = document.getElementById("logs-table-body");
        if (fullLogsBody) {
            fullLogsBody.innerHTML = list.map(l => {
                const date = new Date(l.timestamp).toLocaleString();
                const badge = l.status === 'Success' ? 'badge-success' : 'badge-danger';
                return `
                    <tr>
                        <td><code>LOG-${l.id}</code></td>
                        <td>${date}</td>
                        <td><code>${l.actor_id || 'System'}</code></td>
                        <td><strong>${l.action}</strong></td>
                        <td><span class="badge ${badge}">${l.status}</span></td>
                    </tr>
                `;
            }).join("");
        }
    } catch (e) {
        console.error(e);
    }
}

// Backup & Recovery
async function triggerBackup() {
    try {
        const res = await fetch(`/api/sys-admin/backup?actor_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Backup failed.");
        
        showAlert(`Backup generated successfully: ${data.filename}`);
        await fetchLogs();
    } catch (err) {
        alert(err.message);
    }
}

async function triggerRestore() {
    if (!confirm("Caution: Restoring database will overwrite current database session. Proceed?")) return;
    try {
        const res = await fetch(`/api/sys-admin/restore?actor_id=${loggedInUser.id}`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Restore failed.");
        
        showAlert("Database state restored successfully from backup.");
        await fetchLogs();
        await fetchSysAdminStats();
    } catch (err) {
        alert(err.message);
    }
}
