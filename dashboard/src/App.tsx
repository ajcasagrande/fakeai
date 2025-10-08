import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
// import FineTuningDashboard from './pages/FineTuning';
// import Batches from './pages/Batches';
// import Assistants from './pages/Assistants';
// import VectorStores from './pages/VectorStores';
import DCGMDashboard from './pages/DCGM/DCGMDashboard';
import AIDynamoDashboard from './pages/AIDynamo';
import Chat from './pages/Chat/Chat';
import Metrics from './pages/Metrics';
import KVCacheDashboard from './pages/KVCache';
import BenchmarksDashboard from './pages/Benchmarks';
import Images from './pages/Images/Images';
import Audio from './pages/Audio/Audio';
import Video from './pages/Video/Video';
import { AdminDashboard, AdminLogin } from './pages/Admin';

const App: React.FC = () => {
  // No basename for dev mode - only use /app in production
  const basename = import.meta.env.MODE === 'production' ? '/app' : '';

  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/ai-dynamo" element={<AIDynamoDashboard />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/kv-cache" element={<KVCacheDashboard />} />
        <Route path="/dcgm" element={<DCGMDashboard />} />
        <Route path="/benchmarks" element={<BenchmarksDashboard />} />
        <Route path="/images" element={<Images />} />
        <Route path="/audio" element={<Audio />} />
        <Route path="/video" element={<Video />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        {/* Temporarily disabled - needs Material UI removal
        <Route path="/fine-tuning" element={<FineTuningDashboard />} />
        <Route path="/batches/*" element={<Batches />} />
        <Route path="/assistants/*" element={<Assistants />} />
        <Route path="/vector-stores/*" element={<VectorStores />} />
        <Route path="/dcgm" element={<DCGMDashboard />} />
        */}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
