import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Home } from './pages/Home';
import { Predictor } from './pages/Predictor';
import { Subscription } from './pages/Subscription';
import { News } from './pages/News';
import { FakeNews } from './pages/FakeNews';
import { Chatbot } from './pages/Chatbot';
import { Settings } from './pages/Settings';
import { Portfolio } from './pages/Portfolio';
import { Trade } from './pages/Trade';
import { History } from './pages/History';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/home" replace />} />
                    <Route path="/home" element={<Home />} />
                    <Route path="/portfolio" element={<Portfolio />} />
                    <Route path="/trade" element={<Trade />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/predictor" element={<Predictor />} />
                    <Route path="/subscription" element={<Subscription />} />
                    <Route path="/news" element={<News />} />
                    <Route path="/fakenews" element={<FakeNews />} />
                    <Route path="/chatbot" element={<Chatbot />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
