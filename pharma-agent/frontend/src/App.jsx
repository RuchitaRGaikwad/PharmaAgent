import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Layout
import AppLayout from './components/AppLayout';

// Pages
import ChatPanel from './components/ChatPanel';
import UploadPrescription from './pages/UploadPrescription';
import Medicines from './pages/Medicines';
import Refills from './pages/Refills';
import HealthProfile from './pages/HealthProfile';
import Orders from './pages/Orders';
import SafetyAlerts from './pages/SafetyAlerts';
import SettingsPage from './pages/Settings';

/**
 * App - Root Application Component
 * 
 * Uses nested routing with AppLayout as the shell.
 * ChatPanel is the primary/default route.
 */
function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<ChatPanel />} />
                    <Route path="upload" element={<UploadPrescription />} />
                    <Route path="medicines" element={<Medicines />} />
                    <Route path="refills" element={<Refills />} />
                    <Route path="health" element={<HealthProfile />} />
                    <Route path="orders" element={<Orders />} />
                    <Route path="alerts" element={<SafetyAlerts />} />
                    <Route path="settings" element={<SettingsPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
