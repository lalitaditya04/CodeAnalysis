// Results Page JavaScript - Code Quality Dashboard

class ResultsPage {
    constructor(repositoryId) {
        this.repositoryId = repositoryId;
        this.chartInstances = {};
        this.init();
    }

    init() {
        this.loadResults();
        this.bindEvents();
    }

    bindEvents() {
        // Export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportResults());
        }
    }

    async loadResults() {
        const loadingState = document.getElementById('loadingState');
        const resultsContent = document.getElementById('resultsContent');
        const errorState = document.getElementById('errorState');

        try {
            // Show loading
            loadingState.classList.remove('d-none');
            resultsContent.classList.add('d-none');
            errorState.classList.add('d-none');

            const response = await fetch(`/api/repositories/${this.repositoryId}/detailed-results`);
            const data = await response.json();

            console.log('API Response:', data); // Debug logging
            
            if (data.success && data.data && data.data.scan_result) {
                this.renderResults(data.data);
                loadingState.classList.add('d-none');
                resultsContent.classList.remove('d-none');
            } else {
                throw new Error(data.error || 'No scan results available');
            }
        } catch (error) {
            console.error('Error loading results:', error);
            loadingState.classList.add('d-none');
            errorState.classList.remove('d-none');
            
            // Show more specific error message
            const errorMessage = document.querySelector('#errorState .alert');
            if (errorMessage) {
                errorMessage.innerHTML = `
                    <h4 class="alert-heading">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error Loading Results
                    </h4>
                    <p>${error.message}</p>
                    <hr>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-refresh me-2"></i>Try Again
                    </button>
                `;
            }
        }
    }

    renderResults(data) {
        try {
            const { repository, scan_result, understanding_score, file_analyses, function_analyses } = data;

            // Store scan result for other methods
            this.scanResult = scan_result;

            // Update header information
            const primaryLanguageEl = document.getElementById('primaryLanguage');
            if (primaryLanguageEl && scan_result && scan_result.primary_language) {
                primaryLanguageEl.textContent = scan_result.primary_language;
            }

            // Update overview cards
            if (scan_result) {
                this.updateOverviewCards(scan_result, understanding_score);
            }

            // Render charts
            if (scan_result) {
                this.renderCharts(scan_result);
            }

            // Update detailed metrics
            if (scan_result) {
                this.updateDetailedMetrics(scan_result);
            }

            // Render file analysis table
            if (file_analyses) {
                this.renderFileAnalysis(file_analyses);
            }

            // Render understanding score breakdown
            if (understanding_score) {
                this.renderScoreBreakdown(understanding_score);
            }

            // Add animations
            this.addAnimations();
            
        } catch (error) {
            console.error('Error rendering results:', error);
            throw new Error(`Failed to render results: ${error.message}`);
        }
    }

    updateOverviewCards(scanResult, understandingScore) {
        // Understanding Score
        const score = understandingScore?.readability_score || 0;
        const difficulty = understandingScore?.difficulty_level || 'Unknown';
        
        const understandingScoreEl = document.getElementById('understandingScore');
        const difficultyBadgeEl = document.getElementById('difficultyBadge');
        
        if (understandingScoreEl) understandingScoreEl.textContent = score;
        if (difficultyBadgeEl) {
            difficultyBadgeEl.textContent = difficulty;
            difficultyBadgeEl.className = `badge ${this.getDifficultyBadgeClass(difficulty)}`;
        }

        // Complexity Score
        const complexityScoreEl = document.getElementById('complexityScore');
        const complexityBadgeEl = document.getElementById('complexityBadge');
        
        if (complexityScoreEl) {
            complexityScoreEl.textContent = scanResult.complexity_score?.toFixed(1) || '0.0';
        }
        if (complexityBadgeEl) {
            complexityBadgeEl.textContent = scanResult.complexity_category || 'Simple';
            complexityBadgeEl.className = `badge ${this.getComplexityBadgeClass(scanResult.complexity_category)}`;
        }

        // Maintainability Score
        const maintainabilityScoreEl = document.getElementById('maintainabilityScore');
        const maintainabilityBadgeEl = document.getElementById('maintainabilityBadge');
        
        if (maintainabilityScoreEl) {
            maintainabilityScoreEl.textContent = Math.round(scanResult.maintainability_index || 0);
        }
        if (maintainabilityBadgeEl) {
            maintainabilityBadgeEl.textContent = scanResult.maintainability_category || 'Good';
            maintainabilityBadgeEl.className = `badge ${this.getMaintainabilityBadgeClass(scanResult.maintainability_category)}`;
        }

        // Technical Debt
        const technicalDebtEl = document.getElementById('technicalDebt');
        if (technicalDebtEl) {
            const debtHours = Math.round(scanResult.technical_debt_hours || 0);
            technicalDebtEl.textContent = debtHours;
        }
    }

    getDifficultyBadgeClass(difficulty) {
        switch (difficulty?.toLowerCase()) {
            case 'easy': return 'bg-success text-white';
            case 'moderate': return 'bg-info text-white';
            case 'challenging': return 'bg-warning text-dark';
            case 'difficult': return 'bg-danger text-white';
            default: return 'bg-light text-dark';
        }
    }

    getComplexityBadgeClass(category) {
        switch (category?.toLowerCase()) {
            case 'simple': return 'bg-success text-white';
            case 'moderate': return 'bg-warning text-dark';
            case 'complex': return 'bg-danger text-white';
            default: return 'bg-light text-dark';
        }
    }

    getMaintainabilityBadgeClass(category) {
        switch (category?.toLowerCase()) {
            case 'excellent': return 'bg-success text-white';
            case 'good': return 'bg-info text-white';
            case 'moderate': return 'bg-warning text-dark';
            case 'poor': return 'bg-danger text-white';
            default: return 'bg-light text-dark';
        }
    }

    updateDetailedMetrics(scanResult) {
        // Lines of Code Analysis
        const totalLinesEl = document.getElementById('totalLines');
        const codeLinesEl = document.getElementById('codeLines');
        const commentLinesEl = document.getElementById('commentLines');
        const commentRatioEl = document.getElementById('commentRatio');
        
        if (totalLinesEl) totalLinesEl.textContent = this.formatNumber(scanResult.total_lines || 0);
        if (codeLinesEl) codeLinesEl.textContent = this.formatNumber(scanResult.code_lines || 0);
        if (commentLinesEl) commentLinesEl.textContent = this.formatNumber(scanResult.comment_lines || 0);
        if (commentRatioEl) commentRatioEl.textContent = `${(scanResult.comment_ratio || 0).toFixed(1)}%`;

        // Complexity Analysis
        const simpleFunctionsEl = document.getElementById('simpleFunctions');
        const moderateFunctionsEl = document.getElementById('moderateFunctions');
        const complexFunctionsEl = document.getElementById('complexFunctions');
        const totalFunctionsEl = document.getElementById('totalFunctions');
        
        if (simpleFunctionsEl) simpleFunctionsEl.textContent = this.formatNumber(scanResult.simple_functions || 0);
        if (moderateFunctionsEl) moderateFunctionsEl.textContent = this.formatNumber(scanResult.moderate_functions || 0);
        if (complexFunctionsEl) complexFunctionsEl.textContent = this.formatNumber(scanResult.complex_functions || 0);
        if (totalFunctionsEl) totalFunctionsEl.textContent = this.formatNumber(scanResult.total_functions || 0);

        // Technical Debt Breakdown
        const complexityDebtEl = document.getElementById('complexityDebt');
        const duplicationDebtEl = document.getElementById('duplicationDebt');
        const documentationDebtEl = document.getElementById('documentationDebt');
        const longFunctionDebtEl = document.getElementById('longFunctionDebt');
        
        if (complexityDebtEl) complexityDebtEl.textContent = Math.round(scanResult.complexity_debt_minutes || 0) + ' min';
        if (duplicationDebtEl) duplicationDebtEl.textContent = Math.round(scanResult.duplication_debt_minutes || 0) + ' min';
        if (documentationDebtEl) documentationDebtEl.textContent = Math.round(scanResult.documentation_debt_minutes || 0) + ' min';
        if (longFunctionDebtEl) longFunctionDebtEl.textContent = Math.round(scanResult.long_function_debt_minutes || 0) + ' min';

        // Other metrics
        const filesAnalyzedEl = document.getElementById('filesAnalyzed');
        const duplicationPercentageEl = document.getElementById('duplicationPercentage');
        const complexityRangeEl = document.getElementById('complexityRange');
        
        if (filesAnalyzedEl) filesAnalyzedEl.textContent = scanResult.files_analyzed || 0;
        if (duplicationPercentageEl) duplicationPercentageEl.textContent = (scanResult.duplication_percentage || 0).toFixed(1) + '%';
        if (complexityRangeEl) complexityRangeEl.textContent = `${scanResult.complexity_min || 0} - ${scanResult.complexity_max || 0}`;

        // Generate recommendations
        this.generateRecommendations(scanResult);
    }

    generateRecommendations(scanResult) {
        const recommendationsEl = document.getElementById('recommendationsList');
        if (!recommendationsEl) return;

        const recommendations = [];

        if ((scanResult.comment_ratio || 0) < 10) {
            recommendations.push('• Add more code comments and documentation');
        }
        if ((scanResult.duplication_percentage || 0) > 20) {
            recommendations.push('• Reduce code duplication through refactoring');
        }
        if ((scanResult.complex_functions || 0) > 0) {
            recommendations.push('• Break down complex functions into smaller ones');
        }
        if ((scanResult.maintainability_index || 0) < 50) {
            recommendations.push('• Improve overall code maintainability');
        }
        if ((scanResult.technical_debt_hours || 0) > 10) {
            recommendations.push('• Address technical debt to improve code quality');
        }

        if (recommendations.length === 0) {
            recommendations.push('• Code quality looks good - maintain current standards');
            recommendations.push('• Consider regular code reviews to maintain quality');
        }

        recommendationsEl.innerHTML = recommendations.join('<br>');
    }

    renderScoreBreakdown(understandingScore) {
        const scoreBreakdownEl = document.getElementById('scoreBreakdown');
        if (!scoreBreakdownEl || !understandingScore) return;

        const breakdown = understandingScore.score_breakdown || {};
        const finalScore = understandingScore.readability_score || 0;

        scoreBreakdownEl.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <h6>Final Score: <span class="text-primary">${finalScore}</span></h6>
                        <p class="text-muted mb-0">Difficulty: ${understandingScore.difficulty_level || 'Unknown'}</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-2">
                        <small class="text-muted">Maintainability Impact:</small>
                        <span class="text-success ms-2">+${breakdown.maintainability_impact || 0}</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">Documentation Impact:</small>
                        <span class="text-success ms-2">+${breakdown.documentation_impact || 0}</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">Complexity Impact:</small>
                        <span class="text-danger ms-2">-${Math.abs(breakdown.complexity_impact || 0)}</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">Duplication Impact:</small>
                        <span class="text-danger ms-2">-${Math.abs(breakdown.duplication_impact || 0)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    renderCharts(scanResult) {
        // Ensure charts render with fixed dimensions
        setTimeout(() => {
            this.renderComplexityChart(scanResult);
            this.renderCompositionChart(scanResult);
            this.renderLanguageChart(scanResult);
        }, 100);
    }

    renderComplexityChart(scanResult) {
        const ctx = document.getElementById('complexityChart');
        if (!ctx) return;
        
        // Get parent container for sizing
        const container = ctx.parentElement;
        if (!container) return;
        
        if (this.chartInstances.complexity) {
            this.chartInstances.complexity.destroy();
        }

        // Set fixed canvas dimensions
        ctx.style.width = '100%';
        ctx.style.height = '300px';
        ctx.width = container.offsetWidth || 400;
        ctx.height = 300;

        this.chartInstances.complexity = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Simple', 'Moderate', 'Complex'],
                datasets: [{
                    data: [
                        scanResult.simple_functions || 0,
                        scanResult.moderate_functions || 0,
                        scanResult.complex_functions || 0
                    ],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: false, // Completely disable responsive behavior
                maintainAspectRatio: false,
                animation: false, // Disable all animations
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 14 }
                        }
                    }
                }
            }
        });
    }

    renderCompositionChart(scanResult) {
        const ctx = document.getElementById('compositionChart');
        if (!ctx) return;
        
        // Get parent container for sizing
        const container = ctx.parentElement;
        if (!container) return;
        
        if (this.chartInstances.composition) {
            this.chartInstances.composition.destroy();
        }

        // Set fixed canvas dimensions
        ctx.style.width = '100%';
        ctx.style.height = '300px';
        ctx.width = container.offsetWidth || 400;
        ctx.height = 300;

        this.chartInstances.composition = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Code', 'Comments', 'Blanks'],
                datasets: [{
                    data: [
                        scanResult.code_lines || 0,
                        scanResult.comment_lines || 0,
                        scanResult.blank_lines || 0
                    ],
                    backgroundColor: ['#007bff', '#28a745', '#6c757d'],
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: 'rgba(255,255,255,0.1)'
                }]
            },
            options: {
                responsive: false, // Completely disable responsive behavior
                maintainAspectRatio: false,
                animation: false, // Disable all animations
                plugins: { 
                    legend: { display: false } 
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            maxTicksLimit: 6,
                            font: { size: 12 }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 0,
                            font: { size: 12 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderLanguageChart(scanResult) {
        const ctx = document.getElementById('languageChart');
        if (!ctx) return;
        
        // Get parent container for sizing
        const container = ctx.parentElement;
        if (!container) return;
        
        if (this.chartInstances.language) {
            this.chartInstances.language.destroy();
        }

        // Set fixed canvas dimensions
        ctx.style.width = '100%';
        ctx.style.height = '300px';
        ctx.width = container.offsetWidth || 400;
        ctx.height = 300;

        let languageData = {};
        try {
            languageData = JSON.parse(scanResult.language_distribution || '{}');
        } catch (e) {
            // Fallback to primary language
            languageData[scanResult.primary_language || 'Unknown'] = { percentage: 100 };
        }

        const languages = Object.keys(languageData);
        const percentages = Object.values(languageData).map(lang => lang.percentage || 0);
        
        if (languages.length === 0) {
            languages.push(scanResult.primary_language || 'Unknown');
            percentages.push(100);
        }

        this.chartInstances.language = new Chart(ctx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: languages,
                datasets: [{
                    data: percentages,
                    backgroundColor: this.generateColors(languages.length),
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: false, // Completely disable responsive behavior
                maintainAspectRatio: false,
                animation: false, // Disable all animations
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            maxWidth: 200,
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.label}: ${context.raw.toFixed(1)}%`
                        }
                    }
                }
            }
        });
    }

    renderFileAnalysis(fileAnalyses) {
        const tableBody = document.getElementById('fileAnalysisTable');
        
        if (!fileAnalyses || fileAnalyses.length === 0) {
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted py-4">
                            <i class="fas fa-info-circle me-2"></i>
                            No file analysis data available
                        </td>
                    </tr>
                `;
            }
            return;
        }

        if (tableBody) {
            const rows = fileAnalyses.slice(0, 10).map(file => `
                <tr>
                    <td>
                        <div class="fw-bold">${file.file_name || 'Unknown'}</div>
                        <small class="text-muted">${(file.file_path || '').substring(0, 60)}...</small>
                    </td>
                    <td>${this.formatNumber(file.lines_of_code || 0)}</td>
                    <td>
                        <span class="badge ${this.getComplexityScoreBadgeClass(file.complexity_score || 0)}">
                            ${(file.complexity_score || 0).toFixed(1)}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${this.getMaintainabilityScoreBadgeClass(file.maintainability_index || 0)}">
                            ${Math.round(file.maintainability_index || 0)}
                        </span>
                    </td>
                    <td>${file.function_count || 0}</td>
                    <td>
                        <span class="badge ${this.getPriorityBadgeClass(file.improvement_priority || 'Low')}">
                            ${file.improvement_priority || 'Low'}
                        </span>
                    </td>
                </tr>
            `).join('');

            tableBody.innerHTML = rows;
        }
    }

    getComplexityScoreBadgeClass(score) {
        if (score > 15) return 'bg-danger text-white';
        if (score > 10) return 'bg-warning text-dark';
        if (score > 5) return 'bg-info text-white';
        return 'bg-success text-white';
    }

    getMaintainabilityScoreBadgeClass(score) {
        if (score >= 85) return 'bg-success text-white';
        if (score >= 70) return 'bg-info text-white';
        if (score >= 50) return 'bg-warning text-dark';
        return 'bg-danger text-white';
    }

    getPriorityBadgeClass(priority) {
        switch (priority?.toLowerCase()) {
            case 'critical': return 'bg-danger text-white';
            case 'high': return 'bg-warning text-dark';
            case 'medium': return 'bg-info text-white';
            case 'low': return 'bg-success text-white';
            default: return 'bg-light text-dark';
        }
    }

    async exportResults() {
        try {
            const response = await fetch(`/api/repositories/${this.repositoryId}/detailed-results`);
            const data = await response.json();
            
            if (data.success) {
                const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `analysis-results-${this.repositoryId}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showAlert('Results exported successfully!', 'success');
            } else {
                throw new Error('Failed to export results');
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.showAlert('Export failed. Please try again.', 'danger');
        }
    }

    addAnimations() {
        // Add staggered animations to cards
        const cards = document.querySelectorAll('.metric-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fadeInUp');
        });
    }

    generateColors(count) {
        // More professional color palette
        const colors = [
            '#4F46E5', // Indigo
            '#10B981', // Emerald
            '#F59E0B', // Amber
            '#EF4444', // Red
            '#8B5CF6', // Violet
            '#06B6D4', // Cyan
            '#84CC16', // Lime
            '#F97316', // Orange
            '#EC4899', // Pink
            '#6366F1'  // Blue
        ];
        
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(colors[i % colors.length]);
        }
        return result;
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    showAlert(message, type = 'info') {
        // Create alert container if it doesn't exist
        let alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alertContainer';
            alertContainer.className = 'position-fixed top-0 end-0 p-3';
            alertContainer.style.zIndex = '9999';
            document.body.appendChild(alertContainer);
        }

        const alertId = `alert-${Date.now()}`;
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alertEl = document.getElementById(alertId);
            if (alertEl) {
                alertEl.classList.remove('show');
                setTimeout(() => alertEl.remove(), 150);
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
}

// Initialize results page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure DOM is fully ready
    setTimeout(() => {
        const repositoryId = window.repositoryId;
        if (repositoryId) {
            // Check that key elements exist before initializing
            const requiredElements = ['loadingState', 'resultsContent', 'errorState'];
            const missingElements = requiredElements.filter(id => !document.getElementById(id));
            
            if (missingElements.length > 0) {
                console.error('Missing required elements:', missingElements);
                console.error('Please ensure the HTML template includes all required elements');
                return;
            }
            
            window.resultsPage = new ResultsPage(repositoryId);
        } else {
            console.error('Repository ID not found');
        }
    }, 100);
});

// Handle Chart.js configuration
if (typeof Chart !== 'undefined') {
    // Set global defaults to prevent responsive issues
    Chart.defaults.responsive = false;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.animation = false;
}