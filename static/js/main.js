// Patient Monitoring System - Main JavaScript

// Sidebar Toggle
document.addEventListener('DOMContentLoaded', function() {
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    
    // Check if sidebar state is saved in localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
        content.classList.add('sidebar-collapsed');
    }
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            // Toggle collapsed state
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('sidebar-collapsed');
            
            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }
    
    // Handle mobile responsive behavior
    function handleResize() {
        if (window.innerWidth <= 992) {
            // On mobile, sidebar should be hidden by default
            if (!sidebar.classList.contains('mobile-show')) {
                sidebar.classList.remove('collapsed');
                content.classList.remove('sidebar-collapsed');
            }
        } else {
            // On desktop, restore saved state
            sidebar.classList.remove('mobile-show');
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                sidebar.classList.add('collapsed');
                content.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('collapsed');
                content.classList.remove('sidebar-collapsed');
            }
        }
    }
    
    // Initial check
    handleResize();
    
    // Listen for resize events
    window.addEventListener('resize', handleResize);
    
    // Mobile: Toggle sidebar on button click
    if (window.innerWidth <= 992) {
        if (sidebarCollapse) {
            sidebarCollapse.addEventListener('click', function() {
                sidebar.classList.toggle('mobile-show');
            });
        }
        
        // Close sidebar on mobile when clicking outside
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 992) {
                if (!sidebar.contains(event.target) && 
                    !sidebarCollapse.contains(event.target) &&
                    sidebar.classList.contains('mobile-show')) {
                    sidebar.classList.remove('mobile-show');
                }
            }
        });
    }
});

// Auto-refresh functionality (called by individual pages)
function setupAutoRefresh(callback, interval = 10000) {
    setInterval(callback, interval);
}

// AJAX Helper Functions
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

// Format date/time
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format time only
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

// Show notification (simple alert for now, can be enhanced with toast library)
function showNotification(message, type = 'info') {
    // Ensure a notification container exists (stack notifications)
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = 'position:fixed; top:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:10px; align-items:flex-end;';
        document.body.appendChild(container);
    }

    // Create a notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = 'min-width:300px; box-shadow:0 8px 20px rgba(0,0,0,0.08); background: rgba(255,255,255,0.98); border-left: 6px solid #cbd5e1;';
    // Add a colored left border for the notification based on type
    if (type === 'success') notification.style.borderLeftColor = 'rgba(16, 185, 129, 0.9)';
    if (type === 'danger' || type === 'error') notification.style.borderLeftColor = 'rgba(220,38,38,0.95)';
    if (type === 'warning') notification.style.borderLeftColor = 'rgba(245,158,11,0.95)';
    if (type === 'info') notification.style.borderLeftColor = 'rgba(2,132,199,0.9)';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    container.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        try { notification.remove(); } catch (e) {}
    }, 5000);
}

// Handle form submissions with AJAX
function handleFormSubmit(formId, url, method = 'POST', onSuccess = null) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        try {
            const response = await fetch(url, {
                method: method,
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'ok' || response.ok) {
                if (onSuccess) {
                    onSuccess(data);
                } else {
                    showNotification('Operation completed successfully', 'success');
                }
            } else {
                showNotification(data.error || 'An error occurred', 'danger');
            }
        } catch (error) {
            showNotification('Network error: ' + error.message, 'danger');
        }
    });
}

// Utility to create status badge
function createStatusBadge(status, type = 'default') {
    const badgeClass = {
        'new': 'bg-danger',
        'resolved': 'bg-success',
        'active': 'bg-success',
        'disabled': 'bg-secondary',
        'online': 'bg-success',
        'offline': 'bg-secondary'
    }[status] || 'bg-secondary';
    
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

// Utility to create alert type badge
function createAlertTypeBadge(alertType) {
    const typeColors = {
        'bed_exit': 'bg-danger',
        'temp_out_of_range': 'bg-warning',
        'humidity_out_of_range': 'bg-warning',
        'no_motion': 'bg-info'
    };
    
    const color = typeColors[alertType] || 'bg-secondary';
    return `<span class="badge ${color}">${alertType.replace(/_/g, ' ')}</span>`;
}

// Fall Alert Monitoring
let lastFallAlertId = null;
let fallAlertCheckInterval = null;
let fallAlertModal = null;
let lastFallAlertTimestamp = 0; // epoch ms of last shown fall alert

function initFallAlertMonitoring() {
    // Get modal instance
    const modalElement = document.getElementById('fallAlertModal');
    if (modalElement) {
        fallAlertModal = new bootstrap.Modal(modalElement, {
            backdrop: 'static',
            keyboard: false
        });
    }
    
    // Avoid creating multiple intervals if already initialized
    if (fallAlertCheckInterval) {
        // already monitoring
        return;
    }

    // Check for new fall alerts every 3 seconds
    fallAlertCheckInterval = setInterval(checkForFallAlerts, 3000);

    // Initial check
    checkForFallAlerts();
}

function checkForFallAlerts() {
    fetch('/api/alerts?status=new')
        .then(r => r.json())
        .then(alerts => {
            // Find critical alerts (bed_exit, possible_fall)
            const criticalAlerts = alerts.filter(a => 
                (a.alert_type === 'bed_exit' || a.alert_type === 'possible_fall') && 
                a.status === 'new'
            );
            
            if (criticalAlerts.length > 0) {
                // Get the most recent critical alert
                const latestAlert = criticalAlerts.sort((a, b) => 
                    new Date(b.created_at) - new Date(a.created_at)
                )[0];
                
                // Only show if it's a new alert we haven't seen
                    const now = Date.now();
                    const isSameAsLast = (latestAlert.id === lastFallAlertId);
                    const withinCooldown = (now - (lastFallAlertTimestamp || 0)) < 30000; // 30s cooldown

                    // If modal already visible for this alert, don't re-show
                    const modalElement = document.getElementById('fallAlertModal');
                    const isModalShown = modalElement && modalElement.classList.contains('show');

                    if (!isSameAsLast) {
                        // new alert id -> show it
                        lastFallAlertId = latestAlert.id;
                        lastFallAlertTimestamp = now;
                        showFallAlert(latestAlert);
                    } else if (!isModalShown && !withinCooldown) {
                        // same alert but modal not shown and cooldown passed -> re-show
                        lastFallAlertTimestamp = now;
                        showFallAlert(latestAlert);
                    } else {
                        // otherwise ignore repeated notifications
                    }
            } else {
                // No active critical alerts - hide indicator if modal is not shown
                const modalElement = document.getElementById('fallAlertModal');
                const isModalShown = modalElement && modalElement.classList.contains('show');
                
                if (!isModalShown) {
                    const indicator = document.getElementById('fallAlertIndicator');
                    if (indicator) {
                        indicator.classList.add('d-none');
                    }
                    // Reset last alert ID
                    lastFallAlertId = null;
                }
            }
            
            // Show notifications for other alert types
            const otherAlerts = alerts.filter(a => 
                a.alert_type !== 'bed_exit' && 
                a.alert_type !== 'possible_fall' && 
                a.status === 'new'
            );
            
            otherAlerts.forEach(alert => {
                showAlertNotification(alert);
            });
        })
        .catch(error => {
            console.error('Error checking for fall alerts:', error);
        });
}

function showAlertNotification(alert) {
    // Check if we've already shown this alert
    const alertKey = `alert_${alert.id}`;
    if (sessionStorage.getItem(alertKey)) {
        return; // Already shown
    }
    
    sessionStorage.setItem(alertKey, 'true');
    
    // Determine notification type based on alert type
    let notificationType = 'info';
    let icon = 'fa-info-circle';
    
    if (alert.alert_type === 'fever_warning' || alert.alert_type === 'high_temperature') {
        notificationType = 'warning';
        icon = 'fa-thermometer-half';
    } else if (alert.alert_type === 'long_inactivity' || alert.alert_type === 'restlessness_night') {
        notificationType = 'info';
        icon = 'fa-bed';
    } else if (alert.alert_type === 'low_humidity_danger' || alert.alert_type === 'high_humidity_danger') {
        notificationType = 'warning';
        icon = 'fa-tint';
    }
    
    // Show browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(`${alert.bed_name || 'Bed ' + alert.bed_id}: ${alert.alert_type.replace(/_/g, ' ')}`, {
            body: alert.message,
            tag: `alert-${alert.id}`,
            icon: '/static/images/alert-icon.png'
        });
    }
    
    // Show on-page notification
    showNotification(
        `<i class="fas ${icon}"></i> <strong>${alert.bed_name || 'Bed ' + alert.bed_id}:</strong> ${alert.message}`,
        notificationType
    );
}

function showFallAlert(alert) {
    if (!fallAlertModal) return;
    
    // Update modal content
    document.getElementById('fallAlertBed').textContent = alert.bed_name || `Bed ${alert.bed_id}`;
    document.getElementById('fallAlertRoom').textContent = alert.room_no || 'N/A';
    document.getElementById('fallAlertTime').textContent = new Date(alert.created_at).toLocaleString();
    document.getElementById('fallAlertMessage').textContent = alert.message;
    document.getElementById('fallAlertBedName').textContent = 
        `Fall Risk: ${alert.bed_name || `Bed ${alert.bed_id}`}`;
    
    // Store alert ID for resolving
    const modalElement = document.getElementById('fallAlertModal');
    modalElement.dataset.alertId = alert.id;
    modalElement.dataset.bedId = alert.bed_id;
    
    // Show fall alert indicator in navbar
    const indicator = document.getElementById('fallAlertIndicator');
    if (indicator) {
        indicator.classList.remove('d-none');
    }
    
    // Show modal
    fallAlertModal.show();
    
    // Play alert sound (if permission granted)
    playAlertSound();
    
    // Request browser notification permission and show notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Fall Risk Alert!', {
            body: `${alert.bed_name || `Bed ${alert.bed_id}`}: ${alert.message}`,
            tag: 'fall-alert',
            requireInteraction: true,
            badge: '/static/images/alert-icon.png'
        });
    } else if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Fall Risk Alert!', {
                    body: `${alert.bed_name || `Bed ${alert.bed_id}`}: ${alert.message}`,
                    tag: 'fall-alert',
                    requireInteraction: true
                });
            }
        });
    }
    
    // Flash browser tab title
    flashBrowserTitle('⚠️ FALL ALERT!');
}

function playAlertSound() {
    // Create audio context for beep sound
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // High-pitched alert sound
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
        
        // Play 3 beeps
        setTimeout(() => {
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            osc2.frequency.value = 800;
            osc2.type = 'sine';
            gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            osc2.start(audioContext.currentTime);
            osc2.stop(audioContext.currentTime + 0.5);
        }, 600);
        
        setTimeout(() => {
            const osc3 = audioContext.createOscillator();
            const gain3 = audioContext.createGain();
            osc3.connect(gain3);
            gain3.connect(audioContext.destination);
            osc3.frequency.value = 800;
            osc3.type = 'sine';
            gain3.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain3.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            osc3.start(audioContext.currentTime);
            osc3.stop(audioContext.currentTime + 0.5);
        }, 1200);
    } catch (error) {
        console.log('Could not play alert sound:', error);
    }
}

function flashBrowserTitle(alertText) {
    let isOriginal = true;
    const originalTitle = document.title;
    let flashCount = 0;
    const maxFlashes = 20; // Flash for 10 seconds (20 * 0.5s)
    
    const flashInterval = setInterval(() => {
        document.title = isOriginal ? alertText : originalTitle;
        isOriginal = !isOriginal;
        flashCount++;
        
        if (flashCount >= maxFlashes) {
            clearInterval(flashInterval);
            document.title = originalTitle;
        }
    }, 500);
}

function viewBedDetails() {
    const modalElement = document.getElementById('fallAlertModal');
    const bedId = modalElement.dataset.bedId;
    
    if (bedId) {
        // Close modal
        if (fallAlertModal) {
            fallAlertModal.hide();
        }
        
        // Navigate to bed details
        window.location.href = `/beds/${bedId}`;
    }
}

function resolveFallAlert() {
    const modalElement = document.getElementById('fallAlertModal');
    const alertId = modalElement.dataset.alertId;
    
    if (!alertId) return;
    
    fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                if (fallAlertModal) {
                    fallAlertModal.hide();
                }
                
                // Hide fall alert indicator
                const indicator = document.getElementById('fallAlertIndicator');
                if (indicator) {
                    indicator.classList.add('d-none');
                }
                
                showNotification('Fall alert resolved successfully', 'success');
                
                // Reset last alert ID so we can detect new ones
                lastFallAlertId = null;
            } else {
                showNotification('Failed to resolve alert', 'danger');
            }
        })
        .catch(error => {
            console.error('Error resolving alert:', error);
            showNotification('Error resolving alert', 'danger');
        });
}

// Initialize fall alert monitoring when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user is logged in (check for sidebar element)
    if (document.getElementById('sidebar')) {
        initFallAlertMonitoring();
    }
});

// Export functions for use in other scripts
window.PatientMonitor = {
    fetchJSON,
    formatDateTime,
    formatTime,
    showNotification,
    handleFormSubmit,
    createStatusBadge,
    createAlertTypeBadge,
    setupAutoRefresh,
    showFallAlert,
    resolveFallAlert,
    viewBedDetails,
    showAlertNotification
};

// Make functions globally available
window.resolveFallAlert = resolveFallAlert;
window.viewBedDetails = viewBedDetails;

