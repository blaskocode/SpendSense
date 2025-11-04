// SpendSense Operator Dashboard JavaScript

// Auto-detect API base URL (works when served from same origin)
const API_BASE_URL = window.location.origin;

// Tab navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Activate nav button
    event.target.classList.add('active');
    
    // Load data for the tab
    switch(tabName) {
        case 'analytics':
            loadAnalytics();
            break;
        case 'approval':
            loadApprovalQueue();
            break;
        case 'feedback':
            loadFeedbackReview();
            break;
        case 'health':
            loadSystemHealth();
            break;
    }
}

// Load analytics
async function loadAnalytics() {
    const content = document.getElementById('analyticsContent');
    content.innerHTML = '<div class="loading">Loading analytics...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/operator/analytics`);
        const data = await response.json();
        
        let html = '<div class="metrics-grid">';
        
        // Coverage metrics
        if (data.coverage) {
            html += `
                <div class="metric-card">
                    <div class="metric-label">Persona Coverage</div>
                    <div class="metric-value">${data.coverage.persona_coverage}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Recommendation Coverage</div>
                    <div class="metric-value">${data.coverage.recommendation_coverage}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Explainability</div>
                    <div class="metric-value">${data.coverage.explainability_rate}%</div>
                </div>
            `;
        }
        
        // Engagement metrics
        if (data.engagement) {
            html += `
                <div class="metric-card">
                    <div class="metric-label">Helpfulness Score</div>
                    <div class="metric-value">${data.engagement.helpfulness_score}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Engagement Rate</div>
                    <div class="metric-value">${data.engagement.engagement_rate}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Feedback</div>
                    <div class="metric-value">${data.engagement.total_feedback}</div>
                </div>
            `;
        }
        
        html += '</div>';
        
        // Persona distribution
        if (data.persona_distribution) {
            html += '<h3>Persona Distribution</h3><div class="stat-card">';
            for (const [persona, count] of Object.entries(data.persona_distribution)) {
                html += `
                    <div class="stat-row">
                        <span class="stat-label">${persona}</span>
                        <span class="stat-value">${count} users</span>
                    </div>
                `;
            }
            html += '</div>';
        }
        
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `<div class="error-message">Error loading analytics: ${error.message}</div>`;
        console.error('Error:', error);
    }
}

// Load approval queue
async function loadApprovalQueue() {
    const content = document.getElementById('approvalContent');
    content.innerHTML = '<div class="loading">Loading approval queue...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/operator/review`);
        const data = await response.json();
        
        if (data.pending_count === 0) {
            content.innerHTML = '<div class="info-card">No pending recommendations. All recommendations are approved!</div>';
            return;
        }
        
        let html = `<p><strong>Pending Recommendations:</strong> ${data.pending_count}</p>`;
        
        data.recommendations.forEach(rec => {
            html += `
                <div class="approval-item pending">
                    <h3>${escapeHtml(rec.title)}</h3>
                    <p><strong>Type:</strong> ${rec.type} | <strong>User:</strong> ${rec.user_id} | <strong>Persona:</strong> ${rec.persona_name}</p>
                    <div class="rationale">${escapeHtml(rec.rationale)}</div>
                    <div class="approval-actions">
                        <button class="approve-btn" onclick="approveRecommendation('${rec.recommendation_id}')">
                            ✅ Approve
                        </button>
                        <button class="reject-btn" onclick="overrideRecommendation('${rec.recommendation_id}')">
                            ⚠️ Override
                        </button>
                    </div>
                </div>
            `;
        });
        
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `<div class="error-message">Error loading approval queue: ${error.message}</div>`;
        console.error('Error:', error);
    }
}

// Approve recommendation
async function approveRecommendation(recommendationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/operator/approve/${recommendationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                operator_notes: 'Approved via operator dashboard'
            })
        });
        
        if (response.ok) {
            alert('Recommendation approved!');
            loadApprovalQueue();
        } else {
            alert('Error approving recommendation');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error approving recommendation');
    }
}

// Override recommendation
async function overrideRecommendation(recommendationId) {
    const customTitle = prompt('Enter custom title (or leave empty):');
    const customRationale = prompt('Enter custom rationale (or leave empty):');
    
    try {
        const response = await fetch(`${API_BASE_URL}/operator/override/${recommendationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                custom_title: customTitle || null,
                custom_rationale: customRationale || null,
                operator_notes: 'Overridden via operator dashboard'
            })
        });
        
        if (response.ok) {
            alert('Recommendation overridden!');
            loadApprovalQueue();
        } else {
            alert('Error overriding recommendation');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error overriding recommendation');
    }
}

// Load user review
async function loadUserReview() {
    const userId = document.getElementById('reviewUserId').value.trim();
    const content = document.getElementById('reviewContent');
    
    if (!userId) {
        content.innerHTML = '<div class="error-message">Please enter a user ID</div>';
        return;
    }
    
    content.innerHTML = '<div class="loading">Loading user review...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/data/profile/${userId}`);
        const profile = await response.json();
        
        let html = `
            <div class="user-profile">
                <h3>User: ${escapeHtml(userId)}</h3>
                <div class="profile-section">
                    <h4>Persona</h4>
                    <p><strong>Assigned:</strong> ${profile.persona?.persona_name || 'N/A'}</p>
                    <p><strong>Priority:</strong> ${profile.persona?.priority_level || 'N/A'}</p>
                    <p><strong>Signal Strength:</strong> ${profile.persona?.signal_strength?.toFixed(2) || 'N/A'}</p>
                </div>
                
                <div class="profile-section">
                    <h4>30-Day Signals</h4>
                    <table class="signals-table">
                        <tr>
                            <th>Signal</th>
                            <th>Value</th>
                        </tr>
                        ${generateSignalsRows(profile.signals_30d)}
                    </table>
                </div>
                
                <div class="profile-section">
                    <h4>Data Availability</h4>
                    <p>${profile.data_availability || 'Unknown'}</p>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `<div class="error-message">Error loading user review: ${error.message}</div>`;
        console.error('Error:', error);
    }
}

// Generate signals table rows
function generateSignalsRows(signals) {
    if (!signals) return '<tr><td colspan="2">No signals available</td></tr>';
    
    let rows = '';
    
    if (signals.subscriptions) {
        rows += `<tr><td>Subscriptions</td><td>${signals.subscriptions.subscriptions_count || 0}</td></tr>`;
    }
    if (signals.credit) {
        rows += `<tr><td>Credit Utilization</td><td>${signals.credit.credit_utilization?.toFixed(1) || 0}%</td></tr>`;
    }
    if (signals.savings) {
        rows += `<tr><td>Savings Growth</td><td>${signals.savings.savings_growth_rate?.toFixed(1) || 0}%</td></tr>`;
    }
    if (signals.income) {
        rows += `<tr><td>Payroll Detected</td><td>${signals.income.payroll_detected ? 'Yes' : 'No'}</td></tr>`;
    }
    
    return rows || '<tr><td colspan="2">No signals available</td></tr>';
}

// Load feedback review
async function loadFeedbackReview() {
    const content = document.getElementById('feedbackContent');
    content.innerHTML = '<div class="loading">Loading feedback review...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/operator/feedback`);
        const data = await response.json();
        
        let html = '<div class="stat-card">';
        
        if (data.aggregated) {
            html += '<h4>Aggregated Feedback</h4>';
            for (const [key, value] of Object.entries(data.aggregated)) {
                html += `
                    <div class="stat-row">
                        <span class="stat-label">${key.replace(/_/g, ' ')}</span>
                        <span class="stat-value">${value}</span>
                    </div>
                `;
            }
        }
        
        html += '</div>';
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `<div class="error-message">Error loading feedback: ${error.message}</div>`;
        console.error('Error:', error);
    }
}

// Load system health
async function loadSystemHealth() {
    const content = document.getElementById('healthContent');
    content.innerHTML = '<div class="loading">Loading system health...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/operator/health`);
        const data = await response.json();
        
        let html = '<div class="stat-card">';
        html += '<h4>System Health Status</h4>';
        
        if (data.consent) {
            html += `
                <div class="stat-row">
                    <span class="stat-label">Consent Rate</span>
                    <span class="stat-value">${data.consent.consent_rate}%</span>
                </div>
            `;
        }
        
        if (data.latency) {
            html += `
                <div class="stat-row">
                    <span class="stat-label">Estimated Latency</span>
                    <span class="stat-value">${data.latency.estimated_latency_per_user_seconds}s</span>
                </div>
            `;
        }
        
        if (data.data_quality) {
            html += `
                <div class="stat-row">
                    <span class="stat-label">Data Quality</span>
                    <span class="stat-value">${data.data_quality.overall_status}</span>
                </div>
            `;
        }
        
        html += '</div>';
        content.innerHTML = html;
    } catch (error) {
        // Health endpoint might not exist, show basic info
        content.innerHTML = `
            <div class="stat-card">
                <h4>System Health</h4>
                <p>Health monitoring endpoint available. Check API for details.</p>
                <p><a href="${API_BASE_URL}/docs" target="_blank">View API Docs</a></p>
            </div>
        `;
    }
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-load analytics on page load
window.addEventListener('load', function() {
    loadAnalytics();
});

