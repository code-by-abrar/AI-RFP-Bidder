// Nexus Bids AI - Global Frontend Logic

const currentTheme = localStorage.getItem('theme') || 'dark';
if (currentTheme === 'light') {
    document.body.classList.add('light-mode');
}

let API_BASE = '/api';
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:') {
    API_BASE = 'http://localhost:8000/api';
}

function setupThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        const isLight = document.body.classList.contains('light-mode');
        themeToggleBtn.innerHTML = isLight ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            const lightNow = document.body.classList.contains('light-mode');
            localStorage.setItem('theme', lightNow ? 'light' : 'dark');
            themeToggleBtn.innerHTML = lightNow ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        });
    }
}
async function fetchDashboardBids() {
    const bidsGrid = document.getElementById('bids-grid');
    if (!bidsGrid) return;

    try {
        const response = await fetch(`${API_BASE}/bid/`);
        if (!response.ok) throw new Error('Failed to fetch bids');
        const bids = await response.json();

        // Update dashboard stats if we are on index.html
        if (document.getElementById('stat-total-index')) {
            updateIndexStats(bids);
        }

        // Auto-run knowledge base check if on that page
        if (document.getElementById('docs-list')) {
            loadKnowledgeBase();
        }

        if (bids.length === 0) {
            bidsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 4rem; background: var(--surface); border-radius: 20px; border: 1px dashed var(--border);">
                    <i class="fas fa-folder-open" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                    <h3>No Proposals Found</h3>
                    <p style="color: var(--text-muted);">Start by analyzing a new RFP to generate AI bids.</p>
                </div>
            `;
            return;
        }

        bidsGrid.innerHTML = bids.map((bid, index) => {
            const delay = (index % 10) * 0.1;
            return `
                <div class="card animate-fadeIn" style="animation-delay: ${0.4 + delay}s" onclick="location.href='bid.html?id=${bid.id || bid.bid_id}'">
                    <span class="card-tag">${bid.industry || 'General Technology'}</span>
                    <h3 class="card-title">${bid.project_title || 'Unnamed Proposal'}</h3>
                    <p class="card-body">${bid.project_description || 'Analysis completed. Click to view full breakdown and estimations.'}</p>
                    <div class="card-footer">
                        <span><i class="fas fa-clock"></i> ${bid.timeline_weeks || '?'} weeks</span>
                        <div class="status-chip status-success">
                            <i class="fas fa-check-circle"></i> Ready
                        </div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('API Error:', error);
        bidsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; color: var(--error); padding: 3rem;">
                <i class="fas fa-exclamation-triangle fa-2x"></i>
                <p style="margin-top: 1rem;">System synchronization error. Using local cache...</p>
                <button onclick="location.reload()" class="btn btn-outline" style="margin-top: 1rem;">Retry Sync</button>
            </div>
        `;
    }
}

/**
 * Handle RFP Analysis Upload
 */
window.startRFPAnalysis = async (file, title) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);

    const loadingOverlay = document.getElementById('loading-overlay');
    const statusText = loadingOverlay.querySelector('p');
    const loadingHeader = loadingOverlay.querySelector('h2');

    try {
        console.log('Sending RFP to:', `${API_BASE}/rfp/analyze`);
        const response = await fetch(`${API_BASE}/rfp/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Analysis failed');
        
        // Handle Streaming NDJSON
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep partial line in buffer

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const update = JSON.parse(line);
                    console.log('AI Update:', update);

                    // Update UI with progress
                    if (update.message && statusText) statusText.innerText = update.message;
                    if (update.status === 'complete' && update.bid_id) {
                        console.log('Analysis Success. Bid ID:', update.bid_id);
                        if (loadingHeader) loadingHeader.innerText = "Analysis Complete!";
                        if (statusText) statusText.innerText = "Redirecting to your workspace...";
                        setTimeout(() => {
                            window.location.href = `bid.html?id=${update.bid_id}`;
                        }, 1000);
                        return;
                    }
                    if (update.status === 'error') {
                        throw new Error(update.message || 'AI processing error');
                    }

                    if (update.status === 'requires_confirmation') {
                        window.showConfirmationModal(update);
                        return;
                    }
                } catch (e) {
                    console.error('Error parsing stream chunk:', e);
                }
            }
        }

    } catch (error) {
        console.error('Analysis Error:', error);
        alert(`Critical: AI analysis pipeline interrupted. ${error.message}`);
        loadingOverlay.style.display = 'none';
    }
};

/**
 * Load specific bid details
 */
window.loadBidDetails = async (id) => {
    const container = document.getElementById('bid-content');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE}/bid/${id}`);
        if (!response.ok) throw new Error('Bid not found');
        const bid = await response.json();
        const rfp = bid.rfp_extraction || {};
        const tech = bid.technical_proposal || {};
        const estimate = bid.estimation || {};
        
        // Extract tech list safely
        const techList = tech.tech_stack ? Object.values(tech.tech_stack).flat() : 
                       (rfp.tech_requirements ? rfp.tech_requirements.map(t => t.technology) : []);

        container.innerHTML = `
            <div class="animate-fadeIn">
                <div class="page-header" style="margin-bottom: 2rem;">
                    <div class="page-title">
                        <span class="bid-accent">Proposal ID: #NEX-${id.substring(0, 8).toUpperCase()}</span>
                        <h1 style="margin-top: 0.5rem;">${rfp.project_title || 'Analysis Results'}</h1>
                        <p style="color: var(--text-muted);">Generated on ${bid.created_at ? new Date(bid.created_at).toLocaleDateString() : 'Today'}</p>
                    </div>
                </div>

                <div class="detail-row">
                    <div class="detail-box" style="border-color: ${bid.go_no_go_decision?.decision === 'No-Go' ? 'var(--error)' : 'var(--border)'}">
                        <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem;">AI DECISION</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: ${bid.go_no_go_decision?.decision === 'No-Go' ? 'var(--error)' : 'var(--success)'};">
                            ${bid.go_no_go_decision?.decision || 'GO'}
                        </div>
                    </div>
                    <div class="detail-box">
                        <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem;">ESTIMATED COST</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--success);">$${(bid.bid_amount || 0).toLocaleString()}</div>
                    </div>
                    <div class="detail-box">
                        <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem;">TIMELINE</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">${bid.bid_timeline_weeks || '---'} Weeks</div>
                    </div>
                    <div class="detail-box">
                        <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem;">CONFIDENCE SCORE</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-light);">${Math.round((bid.confidence_score || 0.85) * 100)}%</div>
                    </div>
                    <div class="detail-box" style="border-color: ${bid.legal_compliance?.risk_level === 'high' ? 'var(--error)' : 'var(--border)'}">
                        <div style="color: var(--text-muted); font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem;">LEGAL RISK</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: ${bid.legal_compliance?.risk_level === 'low' ? 'var(--success)' : 'var(--error)'}; text-transform: uppercase;">
                            ${bid.legal_compliance?.risk_level || 'UNKNOWN'}
                        </div>
                    </div>
                </div>

                <!-- AI Reasoning -->
                ${bid.go_no_go_decision?.decision === 'No-Go' ? `
                <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; display: flex; align-items: flex-start; gap: 1rem;">
                    <i class="fas fa-exclamation-triangle" style="color: var(--error); margin-top: 0.2rem;"></i>
                    <div>
                        <div style="font-weight: 700; font-size: 0.85rem; color: var(--error); margin-bottom: 0.2rem;">NO-GO REASONING</div>
                        <p style="font-size: 0.9rem; color: var(--text-muted); margin: 0;">${bid.go_no_go_decision?.reasoning || 'High risk factors detected.'}</p>
                    </div>
                </div>` : ''}

                <!-- Legal Summary Ribbon -->
                <div style="background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; padding: 1rem; margin-bottom: 2rem; display: flex; align-items: flex-start; gap: 1rem;">
                    <i class="fas fa-balance-scale" style="color: var(--error); margin-top: 0.2rem;"></i>
                    <div>
                        <div style="font-weight: 700; font-size: 0.85rem; color: var(--error); margin-bottom: 0.2rem;">LEGAL COMPLIANCE OVERVIEW</div>
                        <p style="font-size: 0.9rem; color: var(--text-muted); margin: 0;">${bid.legal_compliance?.overall_summary || 'Legal analysis pending for this proposal.'}</p>
                    </div>
                </div>

                <div class="grid" style="grid-template-columns: 2fr 1fr;">
                    <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 2rem;">
                        <h3 style="margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">Project Overview</h3>
                        <p style="color: var(--text-muted); line-height: 1.8; margin-bottom: 2rem;">${rfp.project_description || 'No description available.'}</p>
                        
                        <h3 style="margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">Core Requirements</h3>
                        <ul style="padding-left: 1.5rem; color: var(--text-muted);">
                            ${(rfp.must_have_features || []).map(f => `<li style="margin-bottom: 0.8rem;">${f}</li>`).join('') || '<li>Standard requirement set analyzed.</li>'}
                        </ul>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 1.5rem;">
                            <h4 style="margin-bottom: 1rem;">Tech Stack Identification</h4>
                            <div style="display: flex; flex-wrap: wrap;">
                                ${techList.length > 0 ? techList.map(t => `<span class="tech-pill">${t}</span>`).join('') : '<span class="tech-pill">General Tech</span>'}
                            </div>
                        </div>
                        
                        <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid var(--primary); border-radius: 20px; padding: 1.5rem;">
                            <h4 style="color: var(--primary-light); margin-bottom: 0.5rem;"><i class="fas fa-magic"></i> AI Bid Insight</h4>
                            <p style="font-size: 0.9rem; color: var(--text-muted);">${estimate.notes || 'This bid has a high probability of success based on historical alignment.'}</p>
                        </div>
                </div>

                <!-- Proposed Team -->
                ${bid.allocated_team?.allocated_team ? `
                <div style="margin-top: 3rem; background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 2rem;">
                    <h3 style="margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;"><i class="fas fa-users" style="color: var(--primary); margin-right: 0.5rem;"></i> Proposed Project Team</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
                        ${bid.allocated_team.allocated_team.map(t => `
                            <div style="background: var(--bg-dark); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                                    <div>
                                        <div style="font-weight: 700; font-size: 1.1rem; color: ${t.assigned_name === 'Hiring Required' ? 'var(--error)' : 'white'};">${t.assigned_name}</div>
                                        <div style="font-size: 0.85rem; color: var(--primary); font-weight: 600; text-transform: uppercase;">${t.role}</div>
                                    </div>
                                    <i class="fas ${t.assigned_name === 'Hiring Required' ? 'fa-user-plus' : 'fa-check-circle'}" style="color: ${t.assigned_name === 'Hiring Required' ? 'var(--error)' : 'var(--success)'}; font-size: 1.2rem;"></i>
                                </div>
                                <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin: 0; flex-grow: 1;">${t.reasoning}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;

        const exportBtn = document.getElementById('export-btn');
        if(exportBtn) {
            exportBtn.style.display = 'inline-block';
            exportBtn.onclick = () => {
                window.location.href = `${API_BASE}/bid/${id}/export`;
            };
        }

    } catch (error) {
        console.error('Bid Detail Error:', error);
        container.innerHTML = `<div style="text-align: center; color: var(--error); padding: 3rem;">Error loading bid detail.</div>`;
    }
};

/**
 * Load Analytics and render charts
 */
window.loadAnalytics = async () => {
    try {
        const response = await fetch(`${API_BASE}/analytics/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        const stats = await response.json();

        // Update basic stats
        document.getElementById('stat-total').innerText = stats.total_proposals;
        document.getElementById('stat-winrate').innerText = `${stats.win_rate}%`;
        document.getElementById('stat-revenue').innerText = `$${stats.total_revenue.toLocaleString()}`;
        document.getElementById('stat-pending').innerText = stats.status_distribution.submitted;

        // Render Status Chart
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Won', 'Lost', 'Submitted', 'Draft'],
                datasets: [{
                    data: [
                        stats.status_distribution.won,
                        stats.status_distribution.lost,
                        stats.status_distribution.submitted,
                        stats.status_distribution.draft
                    ],
                    backgroundColor: ['#10b981', '#ef4444', '#3b82f6', '#94a3b8'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8' } }
                }
            }
        });

        // Render Industry Chart
        const industryCtx = document.getElementById('industryChart').getContext('2d');
        const industries = Object.keys(stats.industry_distribution);
        const industryData = Object.values(stats.industry_distribution);

        new Chart(industryCtx, {
            type: 'bar',
            data: {
                labels: industries,
                datasets: [{
                    label: 'Proposals by Industry',
                    data: industryData,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });

    } catch (error) {
        console.error('Analytics Error:', error);
    }
};

/**
 * Helper to update index summary stats
 */
function updateIndexStats(bids) {
    const totalEl = document.getElementById('stat-total-index');
    const rateEl = document.getElementById('stat-winrate-index');
    
    if (!totalEl || !rateEl) return;

    const won = bids.filter(b => b.status === 'won').length;
    const lost = bids.filter(b => b.status === 'lost').length;
    const rate = (won + lost) > 0 ? Math.round((won / (won + lost)) * 100) : 0;

    totalEl.innerText = bids.length;
    rateEl.innerText = `${rate}%`;
}

/**
 * Knowledge Base Logic
 */
window.loadKnowledgeBase = async () => {
    const listEl = document.getElementById('docs-list');
    const countEl = document.getElementById('doc-count');
    if (!listEl) return;

    try {
        const response = await fetch(`${API_BASE}/knowledge/`);
        const docs = await response.json();
        
        countEl.innerText = `${docs.length} Files`;

        if (docs.length === 0) {
            listEl.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 3rem;">
                    <i class="fas fa-folder-open fa-2x" style="margin-bottom: 1rem;"></i>
                    <p>No documents uploaded yet.</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = docs.map(doc => `
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px solid var(--border);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 40px; height: 40px; background: rgba(139, 92, 246, 0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--primary-light);">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div>
                        <div style="font-weight: 600;">${doc.filename}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Uploaded on ${new Date(doc.created_at).toLocaleDateString()}</div>
                    </div>
                </div>
                <div class="status-chip status-success" style="font-size: 0.7rem;">
                    <i class="fas fa-check"></i> Indexed
                </div>
            </div>
        `).join('');

    } catch (e) {
        console.error('KB Error:', e);
    }
};

window.uploadKnowledgeDoc = async (file) => {
    const statusEl = document.getElementById('upload-status');
    if (statusEl) statusEl.style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/knowledge/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');
        
        // Refresh list
        await loadKnowledgeBase();
        
    } catch (e) {
        alert('Upload Error: ' + e.message);
    } finally {
        if (statusEl) statusEl.style.display = 'none';
    }
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    fetchDashboardBids();
});

// --- GO/NO-GO CONFIRMATION FLOW ---

window.showConfirmationModal = function(update) {
    const overlay = document.getElementById('loading-overlay');
    
    // Replace the inner HTML of the spinner with the dialog
    overlay.innerHTML = `
        <div style="background: var(--surface); padding: 2.5rem; border-radius: 12px; max-width: 500px; text-align: left; box-shadow: 0 10px 40px rgba(0,0,0,0.8); border: 1px solid var(--border); position: relative; z-index: 10000; margin: 2rem auto;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--error);"></i>
                <h2 style="margin: 0; color: white;">AI Decision: No-Go</h2>
            </div>
            
            <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.95rem; line-height: 1.5;">
                The AI has evaluated this proposal and recommends <strong style="color: var(--error);">Not Bidding</strong> due to high-risk factors:
            </p>
            
            <div style="background: rgba(239, 68, 68, 0.05); border-left: 4px solid var(--error); padding: 1rem; margin-bottom: 2rem; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-size: 0.9rem; color: var(--text-primary);">${update.data?.reasoning || update.message}</p>
            </div>
            
            <div style="display: flex; gap: 1rem; justify-content: flex-end;">
                <button id="btn-stop-here" style="background: transparent; color: var(--text-primary); border: 1px solid var(--border); padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 600; flex: 1; transition: all 0.2s;">
                    Stop Here
                </button>
                <button id="btn-generate-anyway" style="background: var(--error); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 600; flex: 1; transition: all 0.2s;">
                    Generate Anyway
                </button>
            </div>
        </div>
    `;

    document.getElementById('btn-stop-here').onclick = () => {
        window.location.href = 'index.html';
    };

    document.getElementById('btn-generate-anyway').onclick = () => {
        // Resume loading state visually
        overlay.innerHTML = `
            <div class="spinner"></div>
            <h3 id="loading-status" style="margin-top: 1.5rem; font-weight: 500;">Resuming proposal generation...</h3>
            <p id="loading-substatus" style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.5rem; max-width: 400px; line-height: 1.5;">
                Starting phase 2...
            </p>
            <div style="width: 300px; height: 4px; background: var(--bg-dark); border-radius: 2px; margin-top: 1.5rem; overflow: hidden;">
                <div id="loading-progress" style="width: 30%; height: 100%; background: var(--primary); transition: width 0.3s ease;"></div>
            </div>
        `;
        // Trigger the continue API call
        window.continueRFPAnalysis(update.bid_id);
    };
};

window.continueRFPAnalysis = async function(bidId) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/rfp/${bidId}/continue`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to resume analysis');

        // Setup streaming
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());
            
            for (const line of lines) {
                try {
                    const update = JSON.parse(line);
                    
                    if (update.status === 'error') {
                        throw new Error(update.message);
                    }
                    
                    if (update.status === 'complete') {
                        window.location.href = `bid.html?id=${update.bid_id}`;
                        return;
                    }
                    
                    // Update UI
                    const statusEl = document.getElementById('loading-status');
                    if (statusEl) statusEl.textContent = update.message;
                    
                    const progressEl = document.getElementById('loading-progress');
                    if (progressEl && update.progress) {
                        progressEl.style.width = `${update.progress}%`;
                    }
                } catch (e) {
                    console.error('Error parsing streaming update:', e);
                }
            }
        }
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Failed to resume analysis: ' + error.message);
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = 'none';
        window.location.href = 'index.html';
    }
};

// --- COMPLIANCE AUTO-FILLER ---
document.addEventListener('DOMContentLoaded', () => {
    const qUpload = document.getElementById('questionnaire-upload');
    const qBtn = document.getElementById('btn-fill-questionnaire');
    const qName = document.getElementById('questionnaire-filename');
    const qStatus = document.getElementById('questionnaire-status');

    if (qUpload && qBtn) {
        qUpload.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                qName.textContent = e.target.files[0].name;
            }
        });

        qBtn.addEventListener('click', async () => {
            if (!qUpload.files || qUpload.files.length === 0) {
                alert('Please select an Excel (.xlsx) file first.');
                return;
            }

            const file = qUpload.files[0];
            // Authentication is mocked on the backend for the demo
            // No strict token required
            
            const formData = new FormData();
            formData.append('file', file);

            // UI feedback
            qBtn.disabled = true;
            qUpload.disabled = true;
            qStatus.style.display = 'block';
            qBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            try {
                const response = await fetch(`${API_BASE}/questionnaire/fill`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to process Excel file');
                }

                // Download the blob
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                // Get filename from response header if possible, or fallback
                const disposition = response.headers.get('content-disposition');
                let filename = file.name.replace('.xlsx', '_Filled.xlsx');
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) { 
                        filename = matches[1].replace(/['"]/g, '');
                    }
                }
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                
                alert('Questionnaire processed successfully! Download started.');

            } catch (error) {
                console.error('Questionnaire error:', error);
                alert(error.message);
            } finally {
                // Reset UI
                qBtn.disabled = false;
                qUpload.disabled = false;
                qStatus.style.display = 'none';
                qName.textContent = '';
                qUpload.value = '';
                qBtn.innerHTML = '<i class="fas fa-magic"></i> Auto-Fill Answers';
            }
        });
    }
});
