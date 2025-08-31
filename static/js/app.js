// QNAP NAS Fan Controller JavaScript

class QNAPController {
    constructor() {
        this.isConnected = false;
        this.connectionCheckInterval = null;
        this.logRefreshInterval = null;
        
        this.initializeEventListeners();
        this.checkConnectionStatus();
        this.startConnectionMonitoring();
    }
    
    initializeEventListeners() {
        // Connection form
        document.getElementById('connectionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.connect();
        });
        
        // Disconnect button
        document.getElementById('disconnectBtn').addEventListener('click', () => {
            this.disconnect();
        });
        
        // Fan speed buttons
        document.querySelectorAll('.fan-speed-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const speed = btn.dataset.speed;
                this.setFanSpeed(speed);
            });
        });
        
        // Quick action buttons
        document.getElementById('autoModeBtn').addEventListener('click', () => {
            this.setFanSpeed('auto');
        });
        
        document.getElementById('maxCoolingBtn').addEventListener('click', () => {
            this.setFanSpeed('max');
        });
        
        // Status and log buttons
        document.getElementById('refreshStatusBtn').addEventListener('click', () => {
            this.getFanStatus();
        });
        
        document.getElementById('refreshLogsBtn').addEventListener('click', () => {
            this.refreshLogs();
        });
        
        document.getElementById('clearLogsBtn').addEventListener('click', () => {
            this.clearLogs();
        });
    }
    
    async connect() {
        const connectBtn = document.getElementById('connectBtn');
        const host = document.getElementById('hostInput').value.trim();
        const username = document.getElementById('usernameInput').value.trim();
        const password = document.getElementById('passwordInput').value;
        const port = parseInt(document.getElementById('portInput').value);
        
        // Validate inputs
        if (!host || !username || !password) {
            this.showAlert('All fields are required', 'danger');
            return;
        }
        
        // Add loading state
        this.setButtonLoading(connectBtn, true);
        
        try {
            const response = await fetch('/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    host: host,
                    username: username,
                    password: password,
                    port: port
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
                this.updateConnectionStatus(true, data.connection_info);
                this.enableFanControls();
                
                // Show QM2 detection message if available
                if (data.qm2_detected) {
                    this.showAlert(`QM2 Card detected: ${data.qm2_detected}`, 'info');
                }
                
                this.getFanStatus();
                this.refreshLogs();
                
                // Clear password field for security
                document.getElementById('passwordInput').value = '';
            } else {
                this.showAlert(data.message, 'danger');
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            console.error('Connection error:', error);
            this.showAlert('Connection failed: Network error', 'danger');
            this.updateConnectionStatus(false);
        } finally {
            this.setButtonLoading(connectBtn, false);
        }
    }
    
    async disconnect() {
        const disconnectBtn = document.getElementById('disconnectBtn');
        this.setButtonLoading(disconnectBtn, true);
        
        try {
            const response = await fetch('/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'info');
                this.updateConnectionStatus(false);
                this.disableFanControls();
            } else {
                this.showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Disconnection error:', error);
            this.showAlert('Disconnection failed: Network error', 'danger');
        } finally {
            this.setButtonLoading(disconnectBtn, false);
        }
    }
    
    async setFanSpeed(speed) {
        if (!this.isConnected) {
            this.showAlert('Not connected to NAS', 'warning');
            return;
        }
        
        // Find and highlight the selected button
        document.querySelectorAll('.fan-speed-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.speed === speed) {
                btn.classList.add('active');
                this.setButtonLoading(btn, true);
            }
        });
        
        try {
            const response = await fetch('/set_fan_speed', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    speed: speed
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
                // Refresh status after setting speed
                setTimeout(() => this.getFanStatus(), 1000);
                this.refreshLogs();
            } else {
                this.showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Set fan speed error:', error);
            this.showAlert('Failed to set fan speed: Network error', 'danger');
        } finally {
            // Remove loading state from all buttons
            document.querySelectorAll('.fan-speed-btn').forEach(btn => {
                this.setButtonLoading(btn, false);
            });
        }
    }
    
    async getFanStatus() {
        if (!this.isConnected) {
            return;
        }
        
        const refreshBtn = document.getElementById('refreshStatusBtn');
        this.setButtonLoading(refreshBtn, true);
        
        try {
            const response = await fetch('/get_fan_status');
            const data = await response.json();
            
            if (data.success) {
                const statusBadge = document.getElementById('currentStatus');
                statusBadge.textContent = data.status;
                statusBadge.className = 'badge bg-success';
            } else {
                const statusBadge = document.getElementById('currentStatus');
                statusBadge.textContent = 'Unknown';
                statusBadge.className = 'badge bg-secondary';
                this.showAlert(data.message, 'warning');
            }
        } catch (error) {
            console.error('Get fan status error:', error);
            this.showAlert('Failed to get fan status: Network error', 'danger');
        } finally {
            this.setButtonLoading(refreshBtn, false);
        }
    }
    
    async refreshLogs() {
        try {
            const response = await fetch('/get_logs');
            const data = await response.json();
            
            if (data.success) {
                this.updateLogDisplay(data.logs);
            } else {
                console.error('Failed to get logs:', data.message);
            }
        } catch (error) {
            console.error('Refresh logs error:', error);
        }
    }
    
    async clearLogs() {
        const clearBtn = document.getElementById('clearLogsBtn');
        this.setButtonLoading(clearBtn, true);
        
        try {
            const response = await fetch('/clear_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateLogDisplay([]);
                this.showAlert(data.message, 'info');
            } else {
                this.showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Clear logs error:', error);
            this.showAlert('Failed to clear logs: Network error', 'danger');
        } finally {
            this.setButtonLoading(clearBtn, false);
        }
    }
    
    async checkConnectionStatus() {
        try {
            const response = await fetch('/connection_status');
            const data = await response.json();
            
            if (data.success) {
                this.updateConnectionStatus(data.is_connected, data.connection_info);
                if (data.is_connected) {
                    this.enableFanControls();
                    this.getFanStatus();
                } else {
                    this.disableFanControls();
                }
            }
        } catch (error) {
            console.error('Connection status check error:', error);
            this.updateConnectionStatus(false);
            this.disableFanControls();
        }
    }
    
    updateConnectionStatus(connected, connectionInfo = null) {
        this.isConnected = connected;
        const indicator = document.getElementById('connectionIndicator');
        const status = document.getElementById('connectionStatus');
        const details = document.getElementById('connectionDetails');
        const disconnectBtn = document.getElementById('disconnectBtn');
        
        if (connected) {
            indicator.innerHTML = '<i class="fas fa-circle text-success"></i>';
            status.textContent = 'Connected';
            status.className = 'fw-bold text-success';
            
            if (connectionInfo) {
                details.textContent = `${connectionInfo.username}@${connectionInfo.host}:${connectionInfo.port} (${connectionInfo.connected_at})`;
                
                // Show QM2 card info if available
                const qm2Info = document.getElementById('qm2Info');
                const qm2CardId = document.getElementById('qm2CardId');
                if (connectionInfo.qm2_enc_sys_id) {
                    qm2CardId.textContent = `QM2 Card: ${connectionInfo.qm2_enc_sys_id}`;
                    qm2Info.style.display = 'block';
                } else {
                    qm2Info.style.display = 'none';
                }
            }
            
            disconnectBtn.style.display = 'inline-block';
        } else {
            indicator.innerHTML = '<i class="fas fa-circle text-danger"></i>';
            status.textContent = 'Disconnected';
            status.className = 'fw-bold text-danger';
            details.textContent = '';
            disconnectBtn.style.display = 'none';
            
            // Hide QM2 info when disconnected
            const qm2Info = document.getElementById('qm2Info');
            qm2Info.style.display = 'none';
        }
    }
    
    enableFanControls() {
        document.getElementById('fanControlDisabled').style.display = 'none';
        document.getElementById('fanControlEnabled').style.display = 'block';
        document.getElementById('refreshStatusBtn').disabled = false;
    }
    
    disableFanControls() {
        document.getElementById('fanControlDisabled').style.display = 'block';
        document.getElementById('fanControlEnabled').style.display = 'none';
        document.getElementById('refreshStatusBtn').disabled = true;
        
        // Reset current status
        const statusBadge = document.getElementById('currentStatus');
        statusBadge.textContent = 'Unknown';
        statusBadge.className = 'badge bg-secondary';
        
        // Remove active states from fan buttons
        document.querySelectorAll('.fan-speed-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    updateLogDisplay(logs) {
        const logContainer = document.getElementById('logContainer');
        
        if (logs.length === 0) {
            logContainer.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="fas fa-list-ul fs-1 mb-3"></i>
                    <h6>No commands executed yet</h6>
                    <p class="mb-0">SSH commands and responses will appear here</p>
                </div>
            `;
            return;
        }
        
        const logHtml = logs.map(log => {
            const entryClass = log.success ? 'success' : 'error';
            const responseHtml = log.success ? 
                `<div class="log-response">${this.escapeHtml(log.response)}</div>` :
                `<div class="log-error">${this.escapeHtml(log.error_message || log.response)}</div>`;
            
            return `
                <div class="log-entry ${entryClass}">
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <span class="log-timestamp">[${log.timestamp}]</span>
                        <span class="badge ${log.success ? 'bg-success' : 'bg-danger'}">${log.success ? 'OK' : 'ERROR'}</span>
                    </div>
                    <div class="log-command">$ ${this.escapeHtml(log.command)}</div>
                    ${responseHtml}
                </div>
            `;
        }).reverse().join(''); // Show newest logs first
        
        logContainer.innerHTML = logHtml;
        
        // Auto-scroll to top to show newest logs
        logContainer.scrollTop = 0;
    }
    
    showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show alert-enter" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-remove alert after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                const alert = new bootstrap.Alert(alertElement);
                alert.close();
            }
        }, 5000);
    }
    
    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    setButtonLoading(button, loading) {
        if (loading) {
            button.classList.add('btn-loading');
            button.disabled = true;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    startConnectionMonitoring() {
        // Check connection status every 30 seconds
        this.connectionCheckInterval = setInterval(() => {
            this.checkConnectionStatus();
        }, 30000);
        
        // Refresh logs every 10 seconds if connected
        this.logRefreshInterval = setInterval(() => {
            if (this.isConnected) {
                this.refreshLogs();
            }
        }, 10000);
    }
    
    destroy() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
        if (this.logRefreshInterval) {
            clearInterval(this.logRefreshInterval);
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.qnapController = new QNAPController();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.qnapController) {
        window.qnapController.destroy();
    }
});
