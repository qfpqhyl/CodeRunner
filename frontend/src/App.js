import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider, useAuth } from './components/AuthContext';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ProductHomePage from './pages/ProductHomePage';
import LoginPage from './pages/LoginPage';
import SystemManagement from './pages/SystemManagement';
import CodeLibraryPage from './pages/CodeLibraryPage';
import EnvironmentPage from './pages/EnvironmentPage';
import APIKeyPage from './pages/APIKeyPage';
import AIConfigPage from './pages/AIConfigPage';
import ProfilePage from './pages/ProfilePage';
import CommunityPage from './pages/CommunityPage';
import CreatePostPage from './pages/CreatePostPage';
import PostDetailPage from './pages/PostDetailPage';
import FollowListPage from './pages/FollowListPage';
import 'antd/dist/reset.css';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AppContent = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      Loading...
    </div>;
  }

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/" /> : <LoginPage />
          }
        />
        <Route
          path="/"
          element={
            <Layout>
              {isAuthenticated ? <HomePage /> : <ProductHomePage />}
            </Layout>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout>
                <SystemManagement />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/code-library"
          element={
            <ProtectedRoute>
              <Layout>
                <CodeLibraryPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/environments"
          element={
            <ProtectedRoute>
              <Layout>
                <EnvironmentPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <Layout>
                <APIKeyPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/ai-configs"
          element={
            <ProtectedRoute>
              <Layout>
                <AIConfigPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Layout>
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/:username"
          element={
            <ProtectedRoute>
              <Layout>
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/community"
          element={
            <ProtectedRoute>
              <Layout>
                <CommunityPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/community/create"
          element={
            <ProtectedRoute>
              <Layout>
                <CreatePostPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/community/post/:postId"
          element={
            <ProtectedRoute>
              <Layout>
                <PostDetailPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/:username/:type"
          element={
            <ProtectedRoute>
              <Layout>
                <FollowListPage />
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
};

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;