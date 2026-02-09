import React from 'react';
import { X, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

/**
 * SafetyPanel - Collapsible Right Safety Dashboard
 */
function SafetyPanel({ isOpen, onClose }) {
    const { t } = useTranslation();

    return (
        <aside className={`safety-panel ${isOpen ? 'open' : 'closed'}`}>
            <div className="panel-header">
                <div className="panel-title">
                    <span className="panel-title-dot"></span>
                    {t('safety_panel.title')}
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
                    <div className="section-title">{t('safety_panel.compliance_status')}</div>
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
                        <div className="compliance-status">{t('safety_panel.regulated')}</div>
                    </div>
                </div>

                {/* AI Confidence */}
                <div className="dashboard-section">
                    <div className="section-title">{t('safety_panel.confidence_meter')}</div>
                    <div className="confidence-meter">
                        <div className="confidence-circle">
                            <div className="confidence-inner">
                                <span className="confidence-label">{t('safety_panel.high')}</span>
                                <span className="confidence-value">95%</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Warnings */}
                <div className="dashboard-section">
                    <div className="section-title">{t('safety_panel.warnings')}</div>
                    <div className="warning-card">
                        <CheckCircle size={18} className="warning-icon" />
                        <span className="warning-text">{t('safety_panel.no_warnings')}</span>
                    </div>
                </div>

                {/* Safety Checks */}
                <div className="dashboard-section">
                    <div className="section-title">{t('safety_panel.recent_checks')}</div>
                    <div className="safety-checks-empty">{t('safety_panel.no_checks')}</div>
                </div>
            </div>
        </aside>
    );
}

export default SafetyPanel;
