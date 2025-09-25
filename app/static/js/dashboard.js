// Dashboard JavaScript - Code Quality Dashboard

class Dashboard {
    constructor() {
        this.repositories = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRepositories();
        this.setupAutoRefresh();
    }

    bindEvents() {
        // Form submission
        document.getElementById('addRepoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addRepository();
        });

        // Auto-refresh toggle
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadRepositories();
            }
        });
    }

    async addRepository() {
        const urlInput = document.getElementById('githubUrl');
        const submitBtn = document.getElementById('addRepoBtn');
        const githubUrl = urlInput.value.trim();

        if (!githubUrl) {
            this.showAlert('Please enter a valid GitHub URL', 'warning');
            return;
        }

        // Validate GitHub URL format
        const githubUrlPattern = /^https?:\/\/(www\.)?github\.com\/[\w\-\.]+\/[\w\-\.]+\/?$/;
        if (!githubUrlPattern.test(githubUrl)) {
            this.showAlert('Please enter a valid GitHub repository URL', 'warning');
            return;
        }

        // Set loading state
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding...';
        submitBtn.disabled = true;

        try {
            const response = await fetch('/api/repositories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ github_url: githubUrl })
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Repository added successfully!', 'success');
                urlInput.value = '';
                this.loadRepositories();
            } else {
                this.showAlert(data.error || 'Failed to add repository', 'danger');
            }
        } catch (error) {
            console.error('Error adding repository:', error);
            this.showAlert('Network error. Please try again.', 'danger');
        } finally {
            // Reset button state
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    async loadRepositories() {
        const loadingSpinner = document.getElementById('loadingSpinner');
        const repositoryList = document.getElementById('repositoryList');
        const emptyState = document.getElementById('emptyState');

        // Show loading
        loadingSpinner.classList.remove('d-none');
        repositoryList.innerHTML = '';
        emptyState.classList.add('d-none');

        try {
            const response = await fetch('/api/repositories');
            const data = await response.json();

            if (data.success) {
                this.repositories = data.repositories;
                this.renderRepositories();
            } else {
                this.showAlert('Failed to load repositories', 'danger');
            }
        } catch (error) {
            console.error('Error loading repositories:', error);
            this.showAlert('Failed to load repositories', 'danger');
        } finally {
            loadingSpinner.classList.add('d-none');
        }
    }

    renderRepositories() {
        const repositoryList = document.getElementById('repositoryList');
        const emptyState = document.getElementById('emptyState');

        if (this.repositories.length === 0) {
            emptyState.classList.remove('d-none');
            return;
        }

        repositoryList.innerHTML = this.repositories.map(repo => this.createRepositoryCard(repo)).join('');
        this.bindRepositoryEvents();
    }

    createRepositoryCard(repo) {
        const languageDisplay = repo.language || 'Unknown';
        const scanDate = repo.latest_scan ? new Date(repo.latest_scan.scan_date).toLocaleDateString() : '';
        
        let actionButtons = '';
        let progressBar = '';
        let statusBadge = '';

        switch (repo.scan_status) {
            case 'pending':
                statusBadge = '<span class="badge bg-secondary">Ready</span>';
                actionButtons = `
                    <button class="btn btn-primary btn-sm" onclick="dashboard.startScan(${repo.id}, '${repo.name}')">
                        Start Scan
                    </button>
                `;
                break;
            case 'scanning':
                statusBadge = '<span class="badge bg-info">Scanning...</span>';
                progressBar = '<div class="progress mt-2" style="height: 3px;"><div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%;"></div></div>';
                actionButtons = `
                    <button class="btn btn-info btn-sm" disabled>
                        <i class="fas fa-spinner fa-spin me-1"></i>Analyzing
                    </button>
                `;
                break;
            case 'completed':
                statusBadge = '<span class="badge bg-success">Complete</span>';
                actionButtons = `
                    <a href="/results/${repo.id}" class="btn btn-success btn-sm me-2">View Results</a>
                    <button class="btn btn-outline-primary btn-sm me-2" onclick="dashboard.startScan(${repo.id}, '${repo.name}')">Rescan</button>
                `;
                break;
            case 'error':
                statusBadge = '<span class="badge bg-danger">Failed</span>';
                actionButtons = `
                    <button class="btn btn-warning btn-sm" onclick="dashboard.startScan(${repo.id}, '${repo.name}')">
                        Retry
                    </button>
                `;
                break;
        }

        return `
            <div class="card repo-card" data-repo-id="${repo.id}">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h6 class="card-title mb-1">
                                <i class="fab fa-github me-2"></i>
                                <a href="${repo.github_url}" target="_blank">${repo.name}</a>
                            </h6>
                            <div class="d-flex align-items-center gap-2">
                                <span class="badge bg-light text-dark border">${languageDisplay}</span>
                                ${statusBadge}
                                ${scanDate ? `<small class="text-muted">Last scan: ${scanDate}</small>` : ''}
                            </div>
                            ${progressBar}
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex justify-content-between align-items-center">
                                <div class="repo-main-actions">
                                    ${actionButtons}
                                </div>
                                <button class="btn btn-outline-danger btn-sm" onclick="dashboard.deleteRepository(${repo.id})" title="Delete Repository">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindRepositoryEvents() {
        // Auto-refresh for scanning repositories
        const scanningRepos = this.repositories.filter(repo => repo.scan_status === 'scanning');
        if (scanningRepos.length > 0) {
            setTimeout(() => this.loadRepositories(), 5000); // Refresh every 5 seconds
        }
    }

    async startScan(repoId, repoName) {
        try {
            // Update repository status immediately to show scanning state
            const repoIndex = this.repositories.findIndex(r => r.id === repoId);
            if (repoIndex !== -1) {
                this.repositories[repoIndex].scan_status = 'scanning';
                this.renderRepositories();
            }

            const response = await fetch(`/api/repositories/${repoId}/scan`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                // Start polling for completion without modal
                this.pollScanStatus(repoId);
            } else {
                this.showAlert(data.error || 'Failed to start analysis', 'danger');
                // Reset status on error
                if (repoIndex !== -1) {
                    this.repositories[repoIndex].scan_status = 'error';
                    this.renderRepositories();
                }
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            this.showAlert('Failed to start analysis', 'danger');
        }
    }

    async pollScanStatus(repoId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/repositories/${repoId}`);
                const data = await response.json();

                if (data.success) {
                    const repo = data.repository;
                    
                    // Update repository in local array
                    const repoIndex = this.repositories.findIndex(r => r.id === repoId);
                    if (repoIndex !== -1) {
                        this.repositories[repoIndex].scan_status = repo.scan_status;
                        this.renderRepositories();
                    }
                    
                    if (repo.scan_status === 'completed') {
                        clearInterval(pollInterval);
                        this.showAlert('✅ Analysis completed! Click "View Results" to see details.', 'success');
                    } else if (repo.scan_status === 'error') {
                        clearInterval(pollInterval);
                        this.showAlert('❌ Analysis failed. Click "Retry" to try again.', 'danger');
                    }
                }
            } catch (error) {
                console.error('Error polling scan status:', error);
            }
        }, 2000); // Poll every 2 seconds

        // Stop polling after 10 minutes
        setTimeout(() => {
            clearInterval(pollInterval);
            this.showAlert('⏱️ Analysis is taking longer than expected. Please check back later.', 'warning');
        }, 600000);
    }

    async deleteRepository(repoId) {
        const repo = this.repositories.find(r => r.id === repoId);
        if (!repo) return;

        const confirmed = confirm(`Are you sure you want to delete "${repo.name}" and all its analysis data?`);
        if (!confirmed) return;

        try {
            const response = await fetch(`/api/repositories/${repoId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showAlert('Repository deleted successfully', 'success');
                this.loadRepositories();
            } else {
                this.showAlert(data.error || 'Failed to delete repository', 'danger');
            }
        } catch (error) {
            console.error('Error deleting repository:', error);
            this.showAlert('Failed to delete repository', 'danger');
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = `alert-${Date.now()}`;
        
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show slideIn" role="alert" id="${alertId}">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle',
            primary: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    setupAutoRefresh() {
        // Refresh repositories every 30 seconds if there are scanning repos
        setInterval(() => {
            const scanningRepos = this.repositories.filter(repo => repo.scan_status === 'scanning');
            if (scanningRepos.length > 0) {
                this.loadRepositories();
            }
        }, 30000);
    }

    // Utility method to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Utility method to format time ago
    timeAgo(date) {
        const now = new Date();
        const diffTime = Math.abs(now - new Date(date));
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.ceil(diffDays / 7)} weeks ago`;
        return `${Math.ceil(diffDays / 30)} months ago`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Handle form validation
(function() {
    'use strict';
    window.addEventListener('load', function() {
        const forms = document.getElementsByClassName('needs-validation');
        Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();