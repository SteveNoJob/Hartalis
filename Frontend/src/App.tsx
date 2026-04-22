import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from "./context/AuthContext";

// We will create these files next!
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Subscriptions from './pages/Subscriptions';
import UsageSettings from './pages/Usage';
import ProfileSettings from './pages/Profile';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import ChatInterface from './pages/Chat';

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/subscriptions" element={<Subscriptions />} />
          <Route path="/usage" element={<UsageSettings />} />
          <Route path="/profile" element={<ProfileSettings />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />          
          <Route path="/chats" element={<ChatInterface />} /> 
        </Routes>
      </Router>
    </AuthProvider>
  );
}