import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { Dashboard } from './pages/merchant/Dashboard';
import { Catalogue } from './pages/merchant/Catalogue';
import { SimulationDashboard } from './pages/merchant/SimulationDashboard';
import { Optimization } from './pages/merchant/Optimization';
import { Transactions } from './pages/merchant/Transactions';
import { Analytics } from './pages/merchant/Analytics';
import { Settings } from './pages/merchant/Settings';
import { BuyerFlow } from './pages/buyer/BuyerFlow';

import { Campaigns } from './pages/merchant/Campaigns';

export const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/catalogue" element={<Catalogue />} />
          <Route path="/simulation" element={<SimulationDashboard />} />
          <Route path="/optimization" element={<Optimization />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/buyer/*" element={<BuyerFlow />} />
          {/* Add more routes here as we build them */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
