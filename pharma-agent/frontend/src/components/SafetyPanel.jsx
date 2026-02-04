import React from 'react';
import { X, CheckCircle } from 'lucide-react';

/**
 * SafetyPanel - Collapsible Right Safety Dashboard
 */
function SafetyPanel({ isOpen, onClose }) {
    return (
        <aside className={`safety-panel ${isOpen ? 'open' : 'closed'}`}>
            <div className="panel-header">
                <div className="panel-title">
                    <span className="panel-title-dot"></span>
                    Real-time Safety Dashboard
                </div>
                <button
                    className="panel-close"
                    onClick={onClose}
                    aria-label="Close safety panel"
                >
                    <X size={16} />
                </button>
            </div>

            <div className="panel-content">
                {/* Compliance Status */}
                <div className="dashboard-section">
                    <div className="section-title">Compliance Status</div>
                    <div className="compliance-card">
                        <div className="compliance-chart">
                            {[35, 45, 30, 50, 40, 55, 45, 60].map((height, i) => (
                                <div
                                    key={i}
                                    className="chart-bar"
                                    style={{ height: `${height}px`, animationDelay: `${i * 0.1}s` }}
                                />
                            ))}
                        </div>
                        <div className="compliance-percentage">98%</div>
                        <div className="compliance-status">Regulated</div>
                    </div>
                </div>

                {/* AI Confidence */}
                <div className="dashboard-section">
                    <div className="section-title">AI Confidence Meter</div>
                    <div className="confidence-meter">
                        <div className="confidence-circle">
                            <div className="confidence-inner">
                                <span className="confidence-label">High</span>
                                <span className="confidence-value">95%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Warnings */}
                <div className="dashboard-section">
                    <div className="section-title">Interaction Warnings</div>
                    <div className="warning-card">
                        <CheckCircle size={18} className="warning-icon" />
                        <span className="warning-text">No active warnings</span>
                    </div>
                </div>

                {/* Safety Checks */}
                <div className="dashboard-section">
                    <div className="section-title">Recent Safety Checks</div>
                    <div className="safety-checks-empty">No recent checks</div>
                </div>
            </div>
        </aside>
    );
}

export default SafetyPanel;
