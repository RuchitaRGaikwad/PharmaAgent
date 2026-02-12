import React from 'react';
import { ChevronDown } from 'lucide-react';

const SettingsCard = ({ icon: Icon, title, type, expanded, onToggle, children }) => {
    return (
        <div className="settings-card">
            <div className="settings-card-header" onClick={onToggle}>
                <div className="settings-card-header-left">
                    <div className={`settings-card-icon ${type}`}>
                        <Icon size={20} />
                    </div>
                    <h3 className="settings-card-title">{title}</h3>
                </div>
                <ChevronDown
                    size={20}
                    className={`settings-card-chevron ${expanded ? 'open' : ''}`}
                />
            </div>
            <div className={`settings-card-content ${expanded ? 'open' : ''}`}>
                <div className="settings-card-body">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default SettingsCard;
