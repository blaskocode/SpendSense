// SpendSense User Dashboard JavaScript

// Auto-detect API base URL (works when served from same origin)
const API_BASE_URL = window.location.origin;

// Load user data and display dashboard
async function loadUserData() {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        showError('Please enter a user ID');
        return;
    }

    const dashboard = document.getElementById('dashboard');
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.style.display = 'none';
    
    // Show loading state without destroying dashboard structure
    dashboard.style.display = 'block';
    
    // Hide all sections and show loading
    const sections = ['consentSection', 'welcomeSection', 'insightsSection', 'planSection', 'offersSection', 'dataInfoSection'];
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) section.style.display = 'none';
    });
    
    // Show loading indicator
    let loadingDiv = document.getElementById('loadingIndicator');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.id = 'loadingIndicator';
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'Loading user data';
        dashboard.insertBefore(loadingDiv, dashboard.firstChild);
    } else {
        loadingDiv.style.display = 'block';
    }

    try {
        // Check consent status
        const consentResponse = await fetch(`${API_BASE_URL}/users/consent/${userId}`);
        const consentData = await consentResponse.json();
        
    // Hide loading indicator
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) loadingDiv.style.display = 'none';
    
    const consentSection = document.getElementById('consentSection');
    const consentRequired = document.getElementById('consentRequired');
    const consentGranted = document.getElementById('consentGranted');
    const welcomeSection = document.getElementById('welcomeSection');
    
    if (!consentData.consent_status) {
        // Show consent required message
        if (consentSection) consentSection.style.display = 'block';
        if (consentRequired) consentRequired.style.display = 'block';
        if (consentGranted) consentGranted.style.display = 'none';
        if (welcomeSection) welcomeSection.style.display = 'none';
        const insightsSection = document.getElementById('insightsSection');
        const planSection = document.getElementById('planSection');
        const offersSection = document.getElementById('offersSection');
        const dataInfoSection = document.getElementById('dataInfoSection');
        if (insightsSection) insightsSection.style.display = 'none';
        if (planSection) planSection.style.display = 'none';
        if (offersSection) offersSection.style.display = 'none';
        if (dataInfoSection) dataInfoSection.style.display = 'none';
        
        // Store userId for consent function
        window.currentUserId = userId;
        return;
    }

    // User has consent - show consent granted message and load full dashboard
    if (consentSection) consentSection.style.display = 'block';
    if (consentRequired) consentRequired.style.display = 'none';
    if (consentGranted) consentGranted.style.display = 'block';
    await loadFullDashboard(userId);
        
    } catch (error) {
        showError(`Error loading user data: ${error.message}`);
        console.error('Error:', error);
    }
}

// Load full dashboard with all data
async function loadFullDashboard(userId) {
    try {
        // Load profile (persona and signals)
        const profileResponse = await fetch(`${API_BASE_URL}/data/profile/${userId}`);
        if (!profileResponse.ok) {
            throw new Error('Failed to load profile');
        }
        const profile = await profileResponse.json();

        // Load recommendations
        const recommendationsResponse = await fetch(`${API_BASE_URL}/data/recommendations/${userId}`);
        if (!recommendationsResponse.ok) {
            throw new Error('Failed to load recommendations');
        }
        const recommendationsData = await recommendationsResponse.json();

        // Display welcome section
        displayWelcome(profile);
        
        // Display insights
        displayInsights(profile);
        
        // Display recommendations
        displayRecommendations(recommendationsData);
        
        // Load and display transactions
        await loadTransactions('initial');
        
        // Display data info
        displayDataInfo(profile);
        
        // Show all sections (safely check for existence)
        const welcomeSection = document.getElementById('welcomeSection');
        const insightsSection = document.getElementById('insightsSection');
        const planSection = document.getElementById('planSection');
        const offersSection = document.getElementById('offersSection');
        const dataInfoSection = document.getElementById('dataInfoSection');
        
        if (welcomeSection) welcomeSection.style.display = 'block';
        if (insightsSection) insightsSection.style.display = 'block';
        if (planSection) planSection.style.display = 'block';
        if (offersSection) offersSection.style.display = 'block';
        const transactionsSection = document.getElementById('transactionsSection');
        if (transactionsSection) transactionsSection.style.display = 'block';
        if (dataInfoSection) dataInfoSection.style.display = 'block';
        
    } catch (error) {
        showError(`Error loading dashboard: ${error.message}`);
        console.error('Error:', error);
    }
}

// Display welcome section
function displayWelcome(profile) {
    const persona = profile.persona;
    const welcomeSection = document.getElementById('welcomeSection');
    if (!persona || !welcomeSection) {
        if (welcomeSection) welcomeSection.style.display = 'none';
        return;
    }
    
    const welcomeMessage = document.getElementById('welcomeMessage');
    const personaInfo = document.getElementById('personaInfo');
    
    if (welcomeMessage) {
        welcomeMessage.textContent = `👋 Welcome! You're a ${persona.persona_name}`;
    }
    if (personaInfo) {
        personaInfo.textContent = `Priority Level: ${persona.priority_level} | Signal Strength: ${persona.signal_strength?.toFixed(2) || 'N/A'}`;
    }
}

// Display behavioral insights
function displayInsights(profile) {
    const insightsList = document.getElementById('insightsList');
    insightsList.innerHTML = '';
    
    const signals30d = profile.signals_30d || {};
    
    const insights = [];
    
    // Subscription insights
    if (signals30d.subscriptions?.subscriptions_count > 0) {
        insights.push({
            name: 'Subscriptions',
            value: `${signals30d.subscriptions.subscriptions_count} active`,
            description: `You have ${signals30d.subscriptions.subscriptions_count} recurring subscriptions`
        });
    }
    
    // Credit insights
    if (signals30d.credit?.credit_utilization > 0) {
        insights.push({
            name: 'Credit Utilization',
            value: `${signals30d.credit.credit_utilization.toFixed(1)}%`,
            description: `Your credit utilization is ${signals30d.credit.credit_utilization.toFixed(1)}%`
        });
    }
    
    // Savings insights
    if (signals30d.savings?.savings_growth_rate !== undefined) {
        insights.push({
            name: 'Savings Growth',
            value: `${signals30d.savings.savings_growth_rate.toFixed(1)}%`,
            description: `Your savings are ${signals30d.savings.savings_growth_rate >= 0 ? 'growing' : 'declining'} at ${Math.abs(signals30d.savings.savings_growth_rate).toFixed(1)}%`
        });
    }
    
    // Income insights
    if (signals30d.income?.payroll_detected) {
        insights.push({
            name: 'Income Stability',
            value: signals30d.income.income_variability < 0.2 ? 'Stable' : 'Variable',
            description: `Payroll detected every ${signals30d.income.payroll_frequency_days || 'N/A'} days`
        });
    }
    
    if (insights.length === 0) {
        insightsList.innerHTML = '<p class="info-card">We\'re still learning about your financial patterns. As we gather more data, your insights will become more personalized.</p>';
        return;
    }
    
    insights.slice(0, 3).forEach(insight => {
        const card = document.createElement('div');
        card.className = 'insight-card';
        card.innerHTML = `
            <h3>${insight.name}</h3>
            <div class="value">${insight.value}</div>
            <p>${insight.description}</p>
        `;
        insightsList.appendChild(card);
    });
}

// Display recommendations
function displayRecommendations(data) {
    const recommendations = data.recommendations || [];
    
    const education = recommendations.filter(r => r.type === 'education');
    const offers = recommendations.filter(r => r.type === 'offer');
    
    // Display education
    const educationList = document.getElementById('educationList');
    if (educationList) {
        educationList.innerHTML = '';
        
        if (education.length === 0) {
            educationList.innerHTML = '<p class="info-card">No education recommendations available at this time.</p>';
        } else {
            education.forEach(rec => {
                const card = createRecommendationCard(rec);
                educationList.appendChild(card);
            });
        }
    }
    
    // Display offers
    const offersList = document.getElementById('offersList');
    if (offersList) {
        offersList.innerHTML = '';
        
        if (offers.length === 0) {
            offersList.innerHTML = '<p class="info-card">No partner offers available at this time.</p>';
        } else {
            offers.forEach(rec => {
                const card = createRecommendationCard(rec);
                offersList.appendChild(card);
            });
        }
    }
    
    // Always show the sections if we have recommendations (even if empty)
    const planSection = document.getElementById('planSection');
    const offersSection = document.getElementById('offersSection');
    if (planSection) planSection.style.display = 'block';
    if (offersSection) offersSection.style.display = 'block';
}

// Create recommendation card element
function createRecommendationCard(rec) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    
    const typeClass = rec.type === 'education' ? 'education' : 'offer';
    
    card.innerHTML = `
        <span class="type-badge ${typeClass}">${rec.type}</span>
        <h3>${escapeHtml(rec.title)}</h3>
        <p class="rationale">${escapeHtml(rec.rationale)}</p>
        <div class="feedback-section">
            <button class="feedback-btn" onclick="submitFeedback('${rec.recommendation_id}', true, false, false)">
                👍 Helpful
            </button>
            <button class="feedback-btn" onclick="submitFeedback('${rec.recommendation_id}', false, false, false)">
                👎 Not Helpful
            </button>
            <button class="feedback-btn" onclick="submitFeedback('${rec.recommendation_id}', null, true, false)">
                ✅ I Applied This
            </button>
        </div>
    `;
    
    return card;
}

// Submit feedback
async function submitFeedback(recommendationId, thumbsUp, helpedMe, appliedThis) {
    const userId = document.getElementById('userId').value.trim();
    
    try {
        const response = await fetch(`${API_BASE_URL}/data/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recommendation_id: recommendationId,
                user_id: userId,
                thumbs_up: thumbsUp,
                helped_me: helpedMe,
                applied_this: appliedThis
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Feedback submitted! Thank you.');
        } else {
            alert('Error submitting feedback. Please try again.');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Error submitting feedback. Please try again.');
    }
}

// Provide consent
async function provideConsent() {
    const userId = window.currentUserId || document.getElementById('userId').value.trim();
    
    if (!userId) {
        alert('Please enter a user ID first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/consent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        if (response.ok) {
            // Update consent UI
            const consentRequired = document.getElementById('consentRequired');
            const consentGranted = document.getElementById('consentGranted');
            if (consentRequired) consentRequired.style.display = 'none';
            if (consentGranted) consentGranted.style.display = 'block';
            
            // Show loading indicator while generating recommendations
            const loadingDiv = document.getElementById('loadingIndicator');
            if (loadingDiv) {
                loadingDiv.textContent = 'Generating your personalized recommendations...';
                loadingDiv.style.display = 'block';
            }
            
            // Reload dashboard (this will generate recommendations if needed)
            await loadFullDashboard(userId);
            
            // Hide loading indicator
            if (loadingDiv) loadingDiv.style.display = 'none';
        } else {
            const errorData = await response.json();
            alert(`Error providing consent: ${errorData.detail || 'Please try again.'}`);
        }
    } catch (error) {
        console.error('Error providing consent:', error);
        alert('Error providing consent. Please try again.');
    }
}

// Revoke consent
async function revokeConsent() {
    const userId = document.getElementById('userId').value.trim();
    
    if (!userId) {
        alert('Please enter a user ID first');
        return;
    }
    
    if (!confirm('Are you sure you want to revoke consent? This will remove all recommendations and insights.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/consent/${userId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            // Update consent UI
            const consentRequired = document.getElementById('consentRequired');
            const consentGranted = document.getElementById('consentGranted');
            if (consentRequired) consentRequired.style.display = 'block';
            if (consentGranted) consentGranted.style.display = 'none';
            
            // Hide dashboard sections
            const welcomeSection = document.getElementById('welcomeSection');
            const insightsSection = document.getElementById('insightsSection');
            const planSection = document.getElementById('planSection');
            const offersSection = document.getElementById('offersSection');
            const transactionsSection = document.getElementById('transactionsSection');
            const dataInfoSection = document.getElementById('dataInfoSection');
            
            if (welcomeSection) welcomeSection.style.display = 'none';
            if (insightsSection) insightsSection.style.display = 'none';
            if (planSection) planSection.style.display = 'none';
            if (offersSection) offersSection.style.display = 'none';
            if (transactionsSection) transactionsSection.style.display = 'none';
            if (dataInfoSection) dataInfoSection.style.display = 'none';
            
            // Clear recommendation lists
            const educationList = document.getElementById('educationList');
            const offersList = document.getElementById('offersList');
            const insightsList = document.getElementById('insightsList');
            if (educationList) educationList.innerHTML = '';
            if (offersList) offersList.innerHTML = '';
            if (insightsList) insightsList.innerHTML = '';
            
            alert('Consent revoked successfully. All recommendations have been removed.');
        } else {
            const errorData = await response.json();
            alert(`Error revoking consent: ${errorData.detail || 'Please try again.'}`);
        }
    } catch (error) {
        console.error('Error revoking consent:', error);
        alert('Error revoking consent. Please try again.');
    }
}

// Transaction pagination state
let currentTransactionPage = 0;
const TRANSACTIONS_PER_PAGE = 20;

// Load transactions
async function loadTransactions(direction) {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) return;
    
    try {
        // Calculate offset based on direction
        if (direction === 'next') {
            currentTransactionPage++;
        } else if (direction === 'prev') {
            currentTransactionPage = Math.max(0, currentTransactionPage - 1);
        } else {
            currentTransactionPage = 0;
        }
        
        const offset = currentTransactionPage * TRANSACTIONS_PER_PAGE;
        
        const response = await fetch(`${API_BASE_URL}/data/transactions/${userId}?limit=${TRANSACTIONS_PER_PAGE}&offset=${offset}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Transactions API error:', response.status, errorText);
            throw new Error(`Failed to load transactions: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        
        displayTransactions(data);
        
    } catch (error) {
        console.error('Error loading transactions:', error);
        const transactionsList = document.getElementById('transactionsList');
        if (transactionsList) {
            transactionsList.innerHTML = '<p class="error-message">Error loading transactions. Please try again.</p>';
        }
    }
}

// Display transactions
function displayTransactions(data) {
    const transactionsList = document.getElementById('transactionsList');
    const pagination = document.getElementById('transactionsPagination');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');
    
    if (!transactionsList) return;
    
    const transactions = data.transactions || [];
    const totalCount = data.total_count || 0;
    const totalPages = Math.ceil(totalCount / TRANSACTIONS_PER_PAGE);
    
    if (transactions.length === 0) {
        transactionsList.innerHTML = '<p class="info-card">No transactions found.</p>';
        if (pagination) pagination.style.display = 'none';
        return;
    }
    
    // Create transactions table
    let html = '<table class="transactions-table"><thead><tr>';
    html += '<th>Date</th>';
    html += '<th>Merchant</th>';
    html += '<th>Category</th>';
    html += '<th>Amount</th>';
    html += '<th>Account</th>';
    html += '<th>Status</th>';
    html += '</tr></thead><tbody>';
    
    transactions.forEach(txn => {
        const amount = txn.amount;
        const amountClass = amount >= 0 ? 'positive' : 'negative';
        const amountDisplay = amount >= 0 ? `+$${amount.toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
        const pendingBadge = txn.pending ? '<span class="pending-badge">Pending</span>' : '';
        
        html += `<tr>`;
        html += `<td>${new Date(txn.date).toLocaleDateString()}</td>`;
        html += `<td>${escapeHtml(txn.merchant_name || 'Unknown')}</td>`;
        html += `<td>${escapeHtml(txn.category || 'Uncategorized')}</td>`;
        html += `<td class="amount ${amountClass}">${amountDisplay}</td>`;
        html += `<td>${escapeHtml(txn.account_name || txn.account_type || 'Unknown')}</td>`;
        html += `<td>${pendingBadge}</td>`;
        html += `</tr>`;
    });
    
    html += '</tbody></table>';
    transactionsList.innerHTML = html;
    
    // Update pagination
    if (pagination && totalPages > 1) {
        pagination.style.display = 'flex';
        if (prevBtn) prevBtn.disabled = currentTransactionPage === 0;
        if (nextBtn) nextBtn.disabled = currentTransactionPage >= totalPages - 1;
        if (pageInfo) {
            pageInfo.textContent = `Page ${currentTransactionPage + 1} of ${totalPages} (${totalCount} total)`;
        }
    } else if (pagination) {
        pagination.style.display = 'none';
    }
}

// Display data information
function displayDataInfo(profile) {
    const dataAvailability = document.getElementById('dataAvailability');
    const lastUpdated = document.getElementById('lastUpdated');
    
    if (dataAvailability) {
        dataAvailability.textContent = profile.data_availability || 'Unknown';
    }
    if (lastUpdated) {
        // Try to get last updated from recommendations
        // For now, show current time
        lastUpdated.textContent = new Date().toLocaleString();
    }
}

// Show error message
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Allow Enter key to submit
document.getElementById('userId').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        loadUserData();
    }
});

