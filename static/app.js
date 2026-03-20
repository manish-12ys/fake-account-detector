const API_BASE = '';

// File upload handling
document.getElementById('analysis-form').addEventListener('submit', analyzeAccount);
document.getElementById('fetch-btn').addEventListener('click', fetchInstagram);

// Clear error when username is edited
document.getElementById('username').addEventListener('input', () => {
    const errorBox = document.getElementById('fetch-error');
    errorBox.classList.add('hidden');
    document.getElementById('skip-section').classList.add('hidden');
});

async function fetchInstagram() {
    const username = document.getElementById('username').value.trim();
    const errorBox = document.getElementById('fetch-error');
    const errorMessage = document.getElementById('error-message');
    
    if (!username) {
        errorMessage.textContent = 'Please enter a username first';
        errorBox.classList.remove('hidden');
        return;
    }

    // Validate username format
    if (!/^[a-zA-Z0-9_.]{1,30}$/.test(username)) {
        errorMessage.textContent = 'Invalid Instagram username format';
        errorBox.classList.remove('hidden');
        return;
    }

    const fetchBtn = document.getElementById('fetch-btn');
    const originalText = fetchBtn.innerHTML;
    fetchBtn.disabled = true;
    fetchBtn.innerHTML = 'Fetching (may take up to 30s)...';
    
    const loading = document.getElementById('loading');
    loading.classList.remove('hidden');
    errorBox.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/fetch-instagram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                login_user: null,
                login_pass: null,
                session_id: null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            let errorMsg = error.error || 'Failed to fetch profile. Check username and try again.';
            
            // Better error messages
            if (errorMsg.includes('Not Found')) {
                errorMsg = `Profile '@${username}' not found. Check the spelling and try again.`;
            } else if (errorMsg.includes('Private')) {
                errorMsg = `This account is private. Try a public account.`;
            } else if (errorMsg.includes('Authentication') || errorMsg.includes('auth')) {
                errorMsg = `Instagram authentication failed. The account may be temporarily blocked.`;
            }
            
            errorMessage.textContent = errorMsg;
            errorBox.classList.remove('hidden');
            document.getElementById('skip-section').classList.remove('hidden');
            return;
        }

        const data = await response.json();
        if (!data.success) {
            errorMessage.textContent = `${data.error}`;
            errorBox.classList.remove('hidden');
            return;
        }

        const profile = data.profile;

        // Populate form with fetched data
        document.getElementById('bio').value = profile.bio || '';
        document.getElementById('followers').value = profile.followers_count || 0;
        document.getElementById('following').value = profile.following_count || 0;
        document.getElementById('posts').value = profile.media_count || 0;
        document.getElementById('profile-pic').value = profile.profile_pic_url ? 1 : 0;

        // Show fetched profile with animation
        const profileDiv = document.getElementById('fetched-profile');
        const profileData = document.getElementById('profile-data');
        profileData.innerHTML = `
            <strong>@${profile.username}</strong><br>
            Followers: <strong>${formatNumber(profile.followers_count)}</strong><br>
            Following: <strong>${formatNumber(profile.following_count)}</strong><br>
            Posts: <strong>${formatNumber(profile.media_count)}</strong><br>
            Profile Picture: <strong>${profile.profile_pic_url ? 'Yes' : 'No'}</strong>
        `;
        profileDiv.classList.remove('hidden');
        document.getElementById('skip-section').classList.add('hidden');
        
        // Scroll to results or form
        setTimeout(() => {
            document.getElementById('analysis-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
        
    } catch (error) {
        errorMessage.textContent = `Network error: ${error.message}`;
        errorBox.classList.remove('hidden');
        document.getElementById('skip-section').classList.remove('hidden');
    } finally {
        loading.classList.add('hidden');
        fetchBtn.disabled = false;
        fetchBtn.innerHTML = originalText;
    }
}

function skipToManual() {
    document.getElementById('fetch-error').classList.add('hidden');
    document.getElementById('skip-section').classList.add('hidden');
    document.getElementById('analysis-form').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function analyzeAccount(e) {
    e.preventDefault();

    const loading = document.getElementById('loading');
    loading.classList.remove('hidden');

    const data = {
        username: document.getElementById('username').value || 'N/A',
        bio: document.getElementById('bio').value,
        followers_count: parseInt(document.getElementById('followers').value) || 0,
        following_count: parseInt(document.getElementById('following').value) || 0,
        media_count: parseInt(document.getElementById('posts').value) || 0,
        has_profile_pic: parseInt(document.getElementById('profile-pic').value)
    };

    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            alert('Analysis Error: ' + (error.error || 'Failed to analyze account'));
            return;
        }

        const result = await response.json();
        if (!result.success) {
            alert('Error: ' + result.error);
            return;
        }
        
        displayResults(result);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        loading.classList.add('hidden');
    }
}

function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    const noResults = document.getElementById('no-results');
    const predictionValueEl = document.getElementById('result-prediction');
    const confidenceEl = document.getElementById('result-confidence');
    const riskScoreEl = document.getElementById('result-risk-score');
    const verdictSummaryEl = document.getElementById('result-verdict');
    const verdictDetailEl = document.getElementById('result-verdict-detail') || verdictSummaryEl;
    const verdictIconEl = document.getElementById('verdict-icon');
    const verdictCard = document.getElementById('verdict-card');
    const resultChip = document.getElementById('result-chip');
    const insightsEl = document.getElementById('result-insights');
    const progressFillEl = document.getElementById('progress-fill');
    const progressTextEl = document.getElementById('progress-text');
    const reasoningEl = document.getElementById('result-reasoning');

    if (!resultsDiv || !noResults) {
        return;
    }

    // Update prediction and confidence
    const predictionText = result.prediction === 'Fake' ? 'FAKE' : 'REAL';
    const fakeProbability = Math.max(0, Math.min(1, Number(result.confidence) || 0));
    // Confidence badge reflects confidence in the selected label, not always fake probability.
    const modelConfidence = result.prediction === 'Fake' ? fakeProbability : 1 - fakeProbability;

    if (predictionValueEl) {
        predictionValueEl.textContent = predictionText;
        predictionValueEl.classList.remove('fake', 'real');
        predictionValueEl.classList.add(result.prediction === 'Fake' ? 'fake' : 'real');
    }

    if (confidenceEl) {
        confidenceEl.textContent = `${Math.round(modelConfidence * 100)}%`;
    }

    // Update progress bar
    if (progressFillEl) {
        progressFillEl.style.width = `${fakeProbability * 100}%`;
    }
    if (progressTextEl) {
        progressTextEl.textContent = `${Math.round(fakeProbability * 100)}% probability of fake account`;
    }

    // Display verdict from backend
    if (verdictSummaryEl) {
        verdictSummaryEl.textContent = result.verdict;
    }
    if (verdictDetailEl) {
        verdictDetailEl.textContent = result.verdict;
    }
    if (reasoningEl) {
        reasoningEl.textContent = result.reasoning;
    }
    if (riskScoreEl) {
        riskScoreEl.textContent = `${result.risk_score}/100`;
    }

    // Change verdict card color and class based on verdict
    const verdictClassMap = {
        'High Risk Fake': 'fake',
        'Suspicious': 'suspicious',
        'Likely Genuine': 'genuine',
    };
    // Use a default style for any new verdict labels returned by backend.
    const cardClass = verdictClassMap[result.verdict] || 'review';

    if (verdictCard) {
        verdictCard.classList.remove('fake', 'suspicious', 'genuine', 'review');
        verdictCard.classList.add(cardClass);
    }

    if (resultChip) {
        resultChip.classList.remove('fake', 'suspicious', 'genuine', 'review');
        resultChip.classList.add(cardClass);
        resultChip.textContent = cardClass === 'fake' ? 'High Alert' : cardClass === 'suspicious' ? 'Caution' : cardClass === 'genuine' ? 'Low Risk' : 'Manual Review';
    }

    if (verdictIconEl) {
        verdictIconEl.textContent = cardClass === 'fake' ? '!' : cardClass === 'suspicious' ? '?' : cardClass === 'genuine' ? '+' : '~';
    }

    const insights = [];
    // Keep highlights compact and action-oriented for quick scanning.
    insights.push(`Risk score: ${result.risk_score}/100.`);
    insights.push(`Model confidence in this decision: ${Math.round(modelConfidence * 100)}%.`);
    if (result.prediction === 'Fake' && result.risk_score >= 70) {
        insights.push('Strong signs of inauthentic behavior. Investigate before trusting the account.');
    } else if (result.prediction === 'Fake') {
        insights.push('Potentially risky profile. Manual review is recommended.');
    } else if (result.risk_score <= 30) {
        insights.push('Low-risk profile based on current behavioral signals.');
    } else {
        insights.push('Mixed signals detected. Treat this result as advisory.');
    }
    insights.push(`Reasoning: ${result.reasoning}`);

    if (insightsEl) {
        insightsEl.innerHTML = insights.map((item) => `<li>${item}</li>`).join('');
    }

    // Show results, hide no results
    resultsDiv.classList.remove('hidden');
    noResults.classList.add('hidden');
    
    // Scroll to results
    setTimeout(() => {
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);
}


function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}
