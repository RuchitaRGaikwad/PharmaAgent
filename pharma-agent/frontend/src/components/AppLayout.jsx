import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import SafetyPanel from './SafetyPanel';
import Header from './Header';

/**
 * AppLayout - Enterprise Agent Console Shell
 * 
 * Structure:
 * - Fixed Header (top bar with status)
 * - Collapsible Left Sidebar (navigation)
 * - Center Workspace (PRIMARY - full height/width)
 * - Collapsible Right Safety Panel (hidden on Settings page)
 */
function AppLayout() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [safetyPanelOpen, setSafetyPanelOpen] = useState(true);
    const [adminMode, setAdminMode] = useState(false);
    const location = useLocation();

    // Check if current page is settings (which has its own status panel)
    const isSettingsPage = location.pathname === '/settings';

    // Auto-collapse panels on mobile/tablet
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth <= 1024) {
                setSafetyPanelOpen(false);
            }
            if (window.innerWidth <= 768) {
                setSidebarCollapsed(true);
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Hide safety panel on settings page
    const showSafetyPanel = safetyPanelOpen && !isSettingsPage;

    return (
        <div className="app-shell">
            {/* Fixed Header */}
            <Header
                adminMode={adminMode}
                setAdminMode={setAdminMode}
                safetyPanelOpen={showSafetyPanel}
                setSafetyPanelOpen={setSafetyPanelOpen}
            />

            {/* Main Layout Container */}
            <div className="app-body">
                {/* Left Sidebar */}
                <Sidebar
                    collapsed={sidebarCollapsed}
                    onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
                    adminMode={adminMode}
                />

                {/* Center Workspace - PRIMARY */}
                <main className={`workspace ${sidebarCollapsed ? 'sidebar-collapsed' : ''} ${showSafetyPanel ? '' : 'panel-closed'}`}>
                    <Outlet />
                </main>

                {/* Right Safety Panel - Hidden on Settings page */}
                {!isSettingsPage && (
                    <SafetyPanel
                        isOpen={safetyPanelOpen}
                        onClose={() => setSafetyPanelOpen(false)}
                    />
                )}
            </div>
        </div>
    );
}

export default AppLayout;
