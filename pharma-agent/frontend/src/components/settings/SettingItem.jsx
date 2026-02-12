import React from 'react';

const SettingItem = ({ label, description, value, loading, onChange, disabled }) => {
    return (
        <div className="setting-item">
            <div className="setting-info">
                <div className="setting-label">{label}</div>
                <div className="setting-description">{description}</div>
            </div>
            <button
                className={`toggle-switch ${value ? 'active' : ''} ${loading ? 'loading' : ''}`}
                onClick={onChange}
                disabled={loading || disabled}
                role="switch"
                aria-checked={value}
            >
                <div className="toggle-knob"></div>
            </button>
        </div>
    );
};

export default SettingItem;
