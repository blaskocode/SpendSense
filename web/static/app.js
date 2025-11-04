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
        
        // Hide loading indicator
        const loadingDiv = document.getElementById('loadingIndicator');
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        // Check if user doesn't exist (404 error)
        if (consentResponse.status === 404) {
            let errorMessage = `User "${userId}" does not exist.`;
            try {
                const errorData = await consentResponse.json();
                if (errorData.detail) {
                    errorMessage += ` ${errorData.detail}`;
                }
            } catch (e) {
                // If JSON parsing fails, use default message
            }
            
            showError(errorMessage);
            
            // Hide all dashboard sections
            const sections = ['consentSection', 'welcomeSection', 'insightsSection', 'planSection', 'offersSection', 'dataInfoSection', 'subscriptionsSection', 'transactionsSection', 'aiConsentSection', 'aiPlanSection'];
            sections.forEach(id => {
                const section = document.getElementById(id);
                if (section) section.style.display = 'none';
            });
            
            return;
        }
        
        // If response is not OK, throw error
        if (!consentResponse.ok) {
            throw new Error(`Failed to check consent: ${consentResponse.status}`);
        }
        
        // Parse consent data (only if response is OK)
        const consentData = await consentResponse.json();
        
        const consentSection = document.getElementById('consentSection');
        const consentRequired = document.getElementById('consentRequired');
        const consentGranted = document.getElementById('consentGranted');
        const welcomeSection = document.getElementById('welcomeSection');
        
        if (!consentData.consent_status) {
        // Show ONLY consent required message - hide everything else
        if (consentSection) consentSection.style.display = 'block';
        if (consentRequired) consentRequired.style.display = 'block';
        if (consentGranted) consentGranted.style.display = 'none';
        
        // Hide ALL dashboard sections
        if (welcomeSection) welcomeSection.style.display = 'none';
        const insightsSection = document.getElementById('insightsSection');
        const planSection = document.getElementById('planSection');
        const offersSection = document.getElementById('offersSection');
        const dataInfoSection = document.getElementById('dataInfoSection');
        const subscriptionsSection = document.getElementById('subscriptionsSection');
        const transactionsSection = document.getElementById('transactionsSection');
        const aiConsentSection = document.getElementById('aiConsentSection');
        const aiPlanSection = document.getElementById('aiPlanSection');
        
        if (insightsSection) insightsSection.style.display = 'none';
        if (planSection) planSection.style.display = 'none';
        if (offersSection) offersSection.style.display = 'none';
        if (dataInfoSection) dataInfoSection.style.display = 'none';
        if (subscriptionsSection) subscriptionsSection.style.display = 'none';
        if (transactionsSection) transactionsSection.style.display = 'none';
        if (aiConsentSection) aiConsentSection.style.display = 'none';
        if (aiPlanSection) aiPlanSection.style.display = 'none';
        
        // Store userId for consent function
        window.currentUserId = userId;
        return;
    }

    // User has consent - show consent granted message and load full dashboard
    if (consentSection) consentSection.style.display = 'block';
    if (consentRequired) consentRequired.style.display = 'none';
    if (consentGranted) consentGranted.style.display = 'block';
    
    // Check AI consent status
    await checkAIConsent(userId);
    
    await loadFullDashboard(userId);
        
    } catch (error) {
        // Hide loading indicator
        const loadingDiv = document.getElementById('loadingIndicator');
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        // Show error message
        showError(`Error loading user data: ${error.message}`);
        console.error('Error:', error);
        
        // Hide all sections on error
        const sections = ['consentSection', 'welcomeSection', 'insightsSection', 'planSection', 'offersSection', 'dataInfoSection', 'subscriptionsSection', 'transactionsSection', 'aiConsentSection', 'aiPlanSection'];
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) section.style.display = 'none';
        });
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

        // Check AI consent status to determine if we should request AI recommendations
        const aiConsentStatus = await checkAIConsent(userId);
        const useAI = aiConsentStatus && document.getElementById('userId').value.trim() === userId;
        
        // Load recommendations (with AI if consented)
        const recommendationsUrl = `${API_BASE_URL}/data/recommendations/${userId}${useAI ? '?use_ai=true' : ''}`;
        const recommendationsResponse = await fetch(recommendationsUrl);
        if (!recommendationsResponse.ok) {
            throw new Error('Failed to load recommendations');
        }
        const recommendationsData = await recommendationsResponse.json();
        
        // Display AI error message if AI was requested but failed
        if (useAI && recommendationsData.ai_error_message) {
            displayAIErrorMessage(recommendationsData.ai_error_message);
        }
        
        // Load AI plan if AI was used
        if (recommendationsData.ai_used) {
            await loadAIPlan(userId);
        }

        // Display welcome section
        displayWelcome(profile);
        
        // Display insights
        displayInsights(profile);
        
        // Display recommendations
        displayRecommendations(recommendationsData);
        
        // Load and display subscriptions
        await loadSubscriptions();
        
        // Initialize date range
        initializeTransactionDateRange();
        
        // Load all transactions in date range for search capability
        await loadAllTransactionsInRange();
        
        // Load and display paginated transactions
        await loadTransactions('initial');
        
        // Display data info
        displayDataInfo(profile);
        
        // Show all sections (safely check for existence)
        const welcomeSection = document.getElementById('welcomeSection');
        const insightsSection = document.getElementById('insightsSection');
        const planSection = document.getElementById('planSection');
        const offersSection = document.getElementById('offersSection');
        const subscriptionsSection = document.getElementById('subscriptionsSection');
        const transactionsSection = document.getElementById('transactionsSection');
        const dataInfoSection = document.getElementById('dataInfoSection');
        const aiConsentSection = document.getElementById('aiConsentSection');
        const aiPlanSection = document.getElementById('aiPlanSection');
        
        if (welcomeSection) welcomeSection.style.display = 'block';
        if (insightsSection) insightsSection.style.display = 'block';
        if (planSection) planSection.style.display = 'block';
        if (offersSection) offersSection.style.display = 'block';
        if (subscriptionsSection) subscriptionsSection.style.display = 'block';
        if (transactionsSection) transactionsSection.style.display = 'block';
        if (dataInfoSection) dataInfoSection.style.display = 'block';
        
        // AI consent section: Hidden by default to save tokens
        // Only show if user has already enabled AI, or show button to enable it
        try {
            const aiConsentResponse = await fetch(`${API_BASE_URL}/users/${userId}/ai-consent`);
            if (aiConsentResponse.ok) {
                const aiConsentData = await aiConsentResponse.json();
                const aiConsentRequired = document.getElementById('aiConsentRequired');
                const aiConsentGranted = document.getElementById('aiConsentGranted');
                const showAIOptionsBtn = document.getElementById('showAIOptionsBtn');
                
                if (aiConsentData.ai_consent_status) {
                    // AI is already enabled - show the AI section with "enabled" state
                    if (aiConsentSection) {
                        aiConsentSection.style.display = 'block';
                        if (aiConsentRequired) aiConsentRequired.style.display = 'none';
                        if (aiConsentGranted) aiConsentGranted.style.display = 'block';
                    }
                    // Hide the "Enable AI" button since it's already enabled
                    if (showAIOptionsBtn) showAIOptionsBtn.style.display = 'none';
                } else {
                    // AI not enabled - hide AI section by default, show button to enable
                    if (aiConsentSection) aiConsentSection.style.display = 'none';
                    // Show "Enable AI Recommendations" button in plan section
                    if (showAIOptionsBtn) showAIOptionsBtn.style.display = 'block';
                }
            }
        } catch (error) {
            console.warn('Error checking AI consent status:', error);
            // On error, hide AI section and show enable button
            if (aiConsentSection) aiConsentSection.style.display = 'none';
            const showAIOptionsBtn = document.getElementById('showAIOptionsBtn');
            if (showAIOptionsBtn) showAIOptionsBtn.style.display = 'block';
        }
        
        // AI plan section is handled by loadAIPlan if AI was used
        
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
                   const subscriptionsSection = document.getElementById('subscriptionsSection');
                   const transactionsSection = document.getElementById('transactionsSection');
                   const dataInfoSection = document.getElementById('dataInfoSection');
                   
                   if (welcomeSection) welcomeSection.style.display = 'none';
                   if (insightsSection) insightsSection.style.display = 'none';
                   if (planSection) planSection.style.display = 'none';
                   if (offersSection) offersSection.style.display = 'none';
                   if (subscriptionsSection) subscriptionsSection.style.display = 'none';
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

// AI Consent Management
async function checkAIConsent(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/ai-consent`);
        if (!response.ok) {
            console.warn('Failed to check AI consent status');
            return false;
        }
        const data = await response.json();
        
        // Update UI - show AI consent section if regular consent is granted
        const consentResponse = await fetch(`${API_BASE_URL}/users/consent/${userId}`);
        const consentData = await consentResponse.json();
        const hasRegularConsent = consentData.consent_status === true;
        
        const aiConsentSection = document.getElementById('aiConsentSection');
        const aiConsentRequired = document.getElementById('aiConsentRequired');
        const aiConsentGranted = document.getElementById('aiConsentGranted');
        
        // Show AI consent section if regular consent is granted (regardless of consent section visibility)
        console.log('AI Consent Check:', {
            hasRegularConsent,
            aiConsentStatus: data.ai_consent_status,
            aiConsentSectionExists: !!aiConsentSection
        });
        
        if (aiConsentSection && hasRegularConsent) {
            aiConsentSection.style.display = 'block';
            console.log('AI consent section set to block');
            
            if (data.ai_consent_status) {
                if (aiConsentRequired) aiConsentRequired.style.display = 'none';
                if (aiConsentGranted) aiConsentGranted.style.display = 'block';
            } else {
                if (aiConsentRequired) aiConsentRequired.style.display = 'block';
                if (aiConsentGranted) aiConsentGranted.style.display = 'none';
            }
        } else {
            if (aiConsentSection) {
                // Hide AI consent section if regular consent is not granted
                aiConsentSection.style.display = 'none';
                console.log('AI consent section hidden - no regular consent');
            } else {
                console.warn('AI consent section element not found in DOM');
            }
        }
        
        return data.ai_consent_status;
    } catch (error) {
        console.error('Error checking AI consent:', error);
        return false;
    }
}

// Show AI consent section when user clicks "Enable AI Recommendations" button
function showAIConsentSection() {
    const aiConsentSection = document.getElementById('aiConsentSection');
    const showAIOptionsBtn = document.getElementById('showAIOptionsBtn');
    
    if (aiConsentSection) {
        // Show the AI consent section
        aiConsentSection.style.display = 'block';
        
        // Scroll to the AI consent section
        aiConsentSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Hide the button since the section is now visible
        if (showAIOptionsBtn) showAIOptionsBtn.style.display = 'none';
    }
}

async function grantAIConsent() {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) {
        alert('Please enter a user ID first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/ai-consent`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to grant AI consent');
        }
        
        // Refresh AI consent status
        await checkAIConsent(userId);
        
        // Show success message
        const aiErrorMessage = document.getElementById('aiErrorMessage');
        if (aiErrorMessage) {
            aiErrorMessage.textContent = 'AI consent granted successfully! Regenerating recommendations with AI...';
            aiErrorMessage.className = 'ai-success-message';
            aiErrorMessage.style.display = 'block';
        }
        
        // Reload recommendations with AI enabled
        await loadFullDashboard(userId);
        
        // Hide success message after reload
        if (aiErrorMessage) {
            setTimeout(() => {
                aiErrorMessage.style.display = 'none';
            }, 5000);
        }
    } catch (error) {
        console.error('Error granting AI consent:', error);
        alert(`Error granting AI consent: ${error.message}`);
    }
}

async function revokeAIConsent() {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) {
        alert('Please enter a user ID first');
        return;
    }
    
    if (!confirm('Are you sure you want to disable AI recommendations? This will remove any AI-generated plans.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/ai-consent`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to revoke AI consent');
        }
        
        // Refresh AI consent status
        await checkAIConsent(userId);
        
        // Hide AI plan section
        const aiPlanSection = document.getElementById('aiPlanSection');
        if (aiPlanSection) aiPlanSection.style.display = 'none';
        
        // Reload recommendations without AI
        await loadFullDashboard(userId);
    } catch (error) {
        console.error('Error revoking AI consent:', error);
        alert(`Error revoking AI consent: ${error.message}`);
    }
}

function displayAIErrorMessage(message) {
    const aiErrorMessage = document.getElementById('aiErrorMessage');
    if (aiErrorMessage) {
        aiErrorMessage.textContent = `⚠️ ${message}`;
        aiErrorMessage.className = 'ai-error-message';
        aiErrorMessage.style.display = 'block';
    }
}

async function loadAIPlan(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/data/ai-plan/${userId}`);
        if (!response.ok) {
            if (response.status === 404) {
                // No AI plan found, that's okay
                return;
            }
            throw new Error('Failed to load AI plan');
        }
        const plan = await response.json();
        
        // Display AI plan
        const aiPlanSection = document.getElementById('aiPlanSection');
        const aiPlanContent = document.getElementById('aiPlanContent');
        
        if (aiPlanSection && aiPlanContent) {
            aiPlanSection.style.display = 'block';
            
            let html = '';
            
            // Plan summary
            if (plan.plan_document && plan.plan_document.plan_summary) {
                html += `<div class="ai-plan-summary"><p>${escapeHtml(plan.plan_document.plan_summary)}</p></div>`;
            }
            
            // Key insights
            if (plan.plan_document && plan.plan_document.key_insights && plan.plan_document.key_insights.length > 0) {
                html += '<div class="ai-plan-insights"><h3>Key Insights</h3><ul>';
                plan.plan_document.key_insights.forEach(insight => {
                    html += `<li>${escapeHtml(insight)}</li>`;
                });
                html += '</ul></div>';
            }
            
            // Action items
            if (plan.plan_document && plan.plan_document.action_items && plan.plan_document.action_items.length > 0) {
                html += '<div class="ai-plan-actions"><h3>Action Items</h3><ul>';
                plan.plan_document.action_items.forEach(action => {
                    html += `<li>${escapeHtml(action)}</li>`;
                });
                html += '</ul></div>';
            }
            
            // Metadata
            if (plan.model_used || plan.tokens_used) {
                html += '<div class="ai-plan-metadata"><small>';
                if (plan.model_used) {
                    html += `Generated using ${escapeHtml(plan.model_used)}`;
                }
                if (plan.tokens_used) {
                    html += ` (${plan.tokens_used} tokens)`;
                }
                html += '</small></div>';
            }
            
            aiPlanContent.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading AI plan:', error);
        // Don't show error to user, just log it
    }
}

// Transaction pagination state
let currentTransactionPage = 0;
const TRANSACTIONS_PER_PAGE = 20;
let allTransactionsData = []; // Store all loaded transactions for filtering
let filteredTransactions = []; // Store filtered transactions
let transactionDateRange = {
    startDate: null,
    endDate: null
}; // Date range for transaction search

// Load transactions
async function loadSubscriptions() {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/data/subscriptions/${userId}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Subscriptions API error:', response.status, errorText);
            throw new Error(`Failed to load subscriptions: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        
        displaySubscriptions(data);
        
    } catch (error) {
        console.error('Error loading subscriptions:', error);
        const subscriptionsList = document.getElementById('subscriptionsList');
        if (subscriptionsList) {
            subscriptionsList.innerHTML = '<p class="error-message">Error loading subscriptions. Please try again.</p>';
        }
    }
}

function displaySubscriptions(data) {
    const subscriptionsSummary = document.getElementById('subscriptionsSummary');
    const subscriptionsList = document.getElementById('subscriptionsList');
    
    if (!subscriptionsList) return;
    
    const subscriptions = data.subscriptions || [];
    const totalCount = data.total_count || 0;
    const totalMonthlyCost = data.total_monthly_cost || 0;
    
    // Display summary
    if (subscriptionsSummary) {
        subscriptionsSummary.innerHTML = `
            <div class="summary-card">
                <div class="summary-item">
                    <span class="summary-label">Total Subscriptions:</span>
                    <span class="summary-value">${totalCount}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Total Monthly Cost:</span>
                    <span class="summary-value">$${totalMonthlyCost.toFixed(2)}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Estimated Annual Cost:</span>
                    <span class="summary-value">$${(totalMonthlyCost * 12).toFixed(2)}</span>
                </div>
            </div>
        `;
    }
    
    if (subscriptions.length === 0) {
        subscriptionsList.innerHTML = '<p class="info-card">No active subscriptions found.</p>';
        return;
    }
    
    // Create subscriptions grid
    let html = '<div class="subscriptions-grid">';
    
    subscriptions.forEach(sub => {
        const firstDate = new Date(sub.first_transaction).toLocaleDateString();
        const lastDate = new Date(sub.last_transaction).toLocaleDateString();
        const duration = sub.transaction_count > 1 ? `${sub.transaction_count} payments` : '1 payment';
        
        html += `
            <div class="subscription-card">
                <div class="subscription-header">
                    <h3 class="subscription-merchant">${escapeHtml(sub.merchant_name)}</h3>
                    <span class="subscription-cost">$${sub.avg_monthly_cost.toFixed(2)}<span class="cost-period">/mo</span></span>
                </div>
                <div class="subscription-details">
                    <div class="subscription-detail-item">
                        <span class="detail-label">Category:</span>
                        <span class="detail-value">${escapeHtml(sub.category)}</span>
                    </div>
                    <div class="subscription-detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value ${sub.is_active ? 'status-active' : 'status-inactive'}">
                            ${sub.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <div class="subscription-detail-item">
                        <span class="detail-label">Payments:</span>
                        <span class="detail-value">${duration}</span>
                    </div>
                    <div class="subscription-detail-item">
                        <span class="detail-label">First Payment:</span>
                        <span class="detail-value">${firstDate}</span>
                    </div>
                    <div class="subscription-detail-item">
                        <span class="detail-label">Last Payment:</span>
                        <span class="detail-value">${lastDate}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    subscriptionsList.innerHTML = html;
}

// Update transaction date range
function updateTransactionDateRange() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        transactionDateRange.startDate = startDateInput.value || null;
        transactionDateRange.endDate = endDateInput.value || null;
        
        // Reload transactions with new date range
        loadTransactions('initial');
    }
}

// Reset date range to past 6 months
function resetTransactionDateRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = startDate.toISOString().split('T')[0];
        endDateInput.value = endDate.toISOString().split('T')[0];
        updateTransactionDateRange();
    }
}

// Initialize date range to past 6 months
function initializeTransactionDateRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        startDateInput.value = startDate.toISOString().split('T')[0];
        endDateInput.value = endDate.toISOString().split('T')[0];
        transactionDateRange.startDate = startDateInput.value;
        transactionDateRange.endDate = endDateInput.value;
    }
}

async function loadTransactions(direction) {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) return;
    
    try {
        // Initialize date range if not set
        if (!transactionDateRange.startDate || !transactionDateRange.endDate) {
            initializeTransactionDateRange();
        }
        
        // Check if there's an active search
        const searchInput = document.getElementById('transactionSearch');
        const hasSearch = searchInput && searchInput.value.trim();
        
        // If searching, load all transactions first, then filter
        if (hasSearch) {
            await loadAllTransactionsInRange();
            filterTransactions();
            return;
        }
        
        // For normal paginated view, use pagination
        const limit = TRANSACTIONS_PER_PAGE;
        
        // Calculate offset based on direction
        if (direction === 'next') {
            currentTransactionPage++;
        } else if (direction === 'prev') {
            currentTransactionPage = Math.max(0, currentTransactionPage - 1);
        } else {
            currentTransactionPage = 0;
        }
        
        const offset = currentTransactionPage * TRANSACTIONS_PER_PAGE;
        
        // Build query parameters for paginated view
        const params = new URLSearchParams();
        params.append('limit', limit);
        params.append('offset', offset);
        if (transactionDateRange.startDate) {
            params.append('start_date', transactionDateRange.startDate);
        }
        if (transactionDateRange.endDate) {
            params.append('end_date', transactionDateRange.endDate);
        }
        
        const response = await fetch(`${API_BASE_URL}/data/transactions/${userId}?${params.toString()}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Transactions API error:', response.status, errorText);
            throw new Error(`Failed to load transactions: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        
        // For paginated view, we still need to load all transactions for search capability
        // But we'll do it in the background so search works immediately
        // Don't overwrite allTransactionsData if we already have it loaded
        if (allTransactionsData.length === 0) {
            // Load all transactions in background for search
            loadAllTransactionsInRange().catch(err => {
                console.warn('Background load of all transactions failed:', err);
            });
        }
        
        // Display paginated results
        displayTransactions(data, false);
        
    } catch (error) {
        console.error('Error loading transactions:', error);
        const transactionsList = document.getElementById('transactionsList');
        if (transactionsList) {
            transactionsList.innerHTML = '<p class="error-message">Error loading transactions. Please try again.</p>';
        }
    }
}

// Filter transactions based on search
async function filterTransactions() {
    const searchInput = document.getElementById('transactionSearch');
    const clearBtn = document.getElementById('clearSearchBtn');
    const resultsCount = document.getElementById('searchResultsCount');
    
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.trim().toLowerCase();
    
    // Show/hide clear button
    if (clearBtn) {
        clearBtn.style.display = searchTerm ? 'block' : 'none';
    }
    
    if (!searchTerm) {
        // No search term - reload transactions with pagination
        loadTransactions('initial');
        if (resultsCount) resultsCount.style.display = 'none';
        return;
    }
    
    // If we don't have all transactions loaded, load them first
    // This ensures we search through ALL transactions in the date range
    if (allTransactionsData.length === 0 || 
        (allTransactionsData.length < TRANSACTIONS_PER_PAGE && !searchTerm)) {
        // Load all transactions in date range for search
        await loadAllTransactionsInRange();
    }
    
    // Filter transactions - search across multiple fields
    filteredTransactions = allTransactionsData.filter(txn => {
        const searchableFields = [
            txn.merchant_name || '',
            txn.category || '',
            txn.category_primary || '',
            txn.category_detailed || '',
            txn.account_name || '',
            txn.account_type || '',
            txn.account_subtype || '',
            txn.payment_channel || '',
            txn.transaction_id || '',
            Math.abs(txn.amount).toString(),
            txn.amount >= 0 ? 'credit deposit' : 'debit withdrawal'
        ].join(' ').toLowerCase();
        
        return searchableFields.includes(searchTerm);
    });
    
    // Display filtered results
    displayTransactions({
        transactions: filteredTransactions,
        total_count: filteredTransactions.length
    }, true);
    
    // Show results count
    if (resultsCount) {
        resultsCount.textContent = `${filteredTransactions.length} result${filteredTransactions.length !== 1 ? 's' : ''} found`;
        resultsCount.style.display = 'block';
    }
}

// Load ALL transactions in the current date range (for search)
async function loadAllTransactionsInRange() {
    const userId = document.getElementById('userId').value.trim();
    if (!userId) return;
    
    try {
        // Initialize date range if not set
        if (!transactionDateRange.startDate || !transactionDateRange.endDate) {
            initializeTransactionDateRange();
        }
        
        // Build query parameters - load ALL transactions (limit=0)
        const params = new URLSearchParams();
        params.append('limit', '0'); // No limit - load all
        if (transactionDateRange.startDate) {
            params.append('start_date', transactionDateRange.startDate);
        }
        if (transactionDateRange.endDate) {
            params.append('end_date', transactionDateRange.endDate);
        }
        
        const response = await fetch(`${API_BASE_URL}/data/transactions/${userId}?${params.toString()}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Transactions API error:', response.status, errorText);
            throw new Error(`Failed to load transactions: ${response.status} - ${errorText}`);
        }
        const data = await response.json();
        
        // Store ALL transactions in date range for filtering
        allTransactionsData = data.transactions || [];
        filteredTransactions = [...allTransactionsData];
        
    } catch (error) {
        console.error('Error loading all transactions:', error);
    }
}

// Clear search
function clearTransactionSearch() {
    const searchInput = document.getElementById('transactionSearch');
    if (searchInput) {
        searchInput.value = '';
        filterTransactions();
    }
}

// Display transactions
function displayTransactions(data, isFiltered = false) {
    const transactionsList = document.getElementById('transactionsList');
    const pagination = document.getElementById('transactionsPagination');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');
    
    if (!transactionsList) return;
    
    const transactions = data.transactions || [];
    const totalCount = data.total_count || 0;
    
    // If filtered, show all results without pagination
    // Otherwise, use pagination
    let transactionsToShow = transactions;
    let totalPages = 1;
    
    if (!isFiltered) {
        // Apply pagination for non-filtered results
        const startIndex = currentTransactionPage * TRANSACTIONS_PER_PAGE;
        const endIndex = startIndex + TRANSACTIONS_PER_PAGE;
        transactionsToShow = transactions.slice(startIndex, endIndex);
        totalPages = Math.ceil(totalCount / TRANSACTIONS_PER_PAGE);
    } else {
        // Hide pagination when filtering
        if (pagination) pagination.style.display = 'none';
    }
    
    if (transactionsToShow.length === 0) {
        const searchInput = document.getElementById('transactionSearch');
        const hasSearch = searchInput && searchInput.value.trim();
        transactionsList.innerHTML = hasSearch 
            ? '<p class="info-card">No transactions found matching your search.</p>'
            : '<p class="info-card">No transactions found.</p>';
        if (pagination && !isFiltered) pagination.style.display = 'none';
        return;
    }
    
    // Create transactions table
    let html = '<table class="transactions-table"><thead><tr>';
    html += '<th style="width: 30px;"></th>'; // Expand/collapse icon
    html += '<th>Date</th>';
    html += '<th>Merchant</th>';
    html += '<th>Category</th>';
    html += '<th>Amount</th>';
    html += '<th>Account</th>';
    html += '<th>Status</th>';
    html += '</tr></thead><tbody>';
    
    transactionsToShow.forEach((txn, index) => {
        const amount = txn.amount;
        const amountClass = amount >= 0 ? 'positive' : 'negative';
        const amountDisplay = amount >= 0 ? `+$${amount.toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
        const pendingBadge = txn.pending ? '<span class="pending-badge">Pending</span>' : '<span class="settled-badge">Settled</span>';
        const dateObj = new Date(txn.date);
        const formattedDate = dateObj.toLocaleDateString();
        const formattedTime = dateObj.toLocaleTimeString();
        
        // Transaction details
        const categoryDisplay = txn.category_detailed && txn.category_detailed !== txn.category_primary 
            ? `${txn.category_primary || 'Uncategorized'} - ${txn.category_detailed}`
            : (txn.category || 'Uncategorized');
        
        html += `<tr class="transaction-row" data-index="${index}" onclick="toggleTransactionDetails(${index})">`;
        html += `<td class="expand-icon" id="icon-${index}">▶</td>`;
        html += `<td>${formattedDate}</td>`;
        html += `<td>${escapeHtml(txn.merchant_name || 'Unknown')}</td>`;
        html += `<td>${escapeHtml(txn.category || 'Uncategorized')}</td>`;
        html += `<td class="amount ${amountClass}">${amountDisplay}</td>`;
        html += `<td>${escapeHtml(txn.account_name || txn.account_type || 'Unknown')}</td>`;
        html += `<td>${pendingBadge}</td>`;
        html += `</tr>`;
        
        // Details row (hidden by default)
        html += `<tr class="transaction-details-row" id="details-${index}" style="display: none;">`;
        html += `<td colspan="7">`;
        html += `<div class="transaction-details">`;
        html += `<div class="details-grid">`;
        html += `<div class="detail-item"><span class="detail-label">Transaction ID:</span><span class="detail-value">${escapeHtml(txn.transaction_id)}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Date & Time:</span><span class="detail-value">${formattedDate} at ${formattedTime}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Merchant:</span><span class="detail-value">${escapeHtml(txn.merchant_name || 'Unknown')}</span></div>`;
        if (txn.merchant_entity_id) {
            html += `<div class="detail-item"><span class="detail-label">Merchant ID:</span><span class="detail-value">${escapeHtml(txn.merchant_entity_id)}</span></div>`;
        }
        html += `<div class="detail-item"><span class="detail-label">Category:</span><span class="detail-value">${escapeHtml(categoryDisplay)}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Amount:</span><span class="detail-value amount ${amountClass}">${amountDisplay}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Account:</span><span class="detail-value">${escapeHtml(txn.account_name || txn.account_type || 'Unknown')}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Account Type:</span><span class="detail-value">${escapeHtml(txn.account_type || 'Unknown')}</span></div>`;
        if (txn.account_subtype) {
            html += `<div class="detail-item"><span class="detail-label">Account Subtype:</span><span class="detail-value">${escapeHtml(txn.account_subtype)}</span></div>`;
        }
        html += `<div class="detail-item"><span class="detail-label">Payment Channel:</span><span class="detail-value">${escapeHtml(txn.payment_channel || 'Unknown')}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Status:</span><span class="detail-value">${txn.pending ? '<span class="status-pending">Pending</span>' : '<span class="status-settled">Settled</span>'}</span></div>`;
        html += `<div class="detail-item"><span class="detail-label">Transaction Type:</span><span class="detail-value">${amount >= 0 ? '<span class="type-credit">Credit (Deposit)</span>' : '<span class="type-debit">Debit (Withdrawal)</span>'}</span></div>`;
        html += `</div>`;
        html += `</div>`;
        html += `</td>`;
        html += `</tr>`;
    });
    
    html += '</tbody></table>';
    transactionsList.innerHTML = html;
    
    // Store transaction data for toggle function
    window.transactionsData = transactionsToShow;
    
    // Update pagination (only if not filtered)
    if (!isFiltered && pagination && totalPages > 1) {
        pagination.style.display = 'flex';
        if (prevBtn) prevBtn.disabled = currentTransactionPage === 0;
        if (nextBtn) nextBtn.disabled = currentTransactionPage >= totalPages - 1;
        if (pageInfo) {
            pageInfo.textContent = `Page ${currentTransactionPage + 1} of ${totalPages} (${totalCount} total)`;
        }
    } else if (pagination && !isFiltered) {
        pagination.style.display = 'none';
    }
}

// Toggle transaction details
function toggleTransactionDetails(index) {
    const detailsRow = document.getElementById(`details-${index}`);
    const icon = document.getElementById(`icon-${index}`);
    
    if (!detailsRow || !icon) return;
    
    if (detailsRow.style.display === 'none') {
        detailsRow.style.display = 'table-row';
        icon.textContent = '▼';
        icon.classList.add('expanded');
    } else {
        detailsRow.style.display = 'none';
        icon.textContent = '▶';
        icon.classList.remove('expanded');
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

