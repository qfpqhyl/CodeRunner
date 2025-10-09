import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const register = (userData) => api.post('/register', userData);
export const login = (credentials) => api.post('/login', credentials);
export const getCurrentUser = () => api.get('/users/me');
export const getUsers = () => api.get('/users');

// Admin endpoints
export const createUser = (userData) => api.post('/admin/users', userData);
export const updateUser = (userId, userData) => api.put(`/admin/users/${userId}`, userData);
export const deleteUser = (userId) => api.delete(`/admin/users/${userId}`);
export const getAllExecutions = () => api.get('/admin/executions');

// User level and stats endpoints
export const getUserLevels = () => api.get('/user-levels');
export const getUserStats = () => api.get('/user-stats');

// Code execution endpoints
export const executeCode = (codeData) => api.post('/execute', codeData);
export const getExecutions = () => api.get('/executions');

// Code library endpoints
export const saveCodeToLibrary = (codeData) => api.post('/code-library', codeData);
export const getCodeLibrary = (params = {}) => api.get('/code-library', { params });
export const getCodeFromLibrary = (codeId) => api.get(`/code-library/${codeId}`);
export const updateCodeInLibrary = (codeId, codeData) => api.put(`/code-library/${codeId}`, codeData);
export const deleteCodeFromLibrary = (codeId) => api.delete(`/code-library/${codeId}`);

// Password change endpoints
export const changePassword = (passwordData) => api.post('/change-password', passwordData);
export const changeUserPasswordByAdmin = (userId, passwordData) => api.post(`/admin/users/${userId}/change-password`, passwordData);

// API Key endpoints
export const createAPIKey = (keyData) => api.post('/api-keys', keyData);
export const getAPIKeys = () => api.get('/api-keys');
export const toggleAPIKey = (keyId) => api.put(`/api-keys/${keyId}/toggle`);
export const deleteAPIKey = (keyId) => api.delete(`/api-keys/${keyId}`);

// System Logs endpoints (Admin only)
export const getSystemLogs = (params = {}) => api.get('/admin/logs', { params });
export const getLogStatistics = (params = {}) => api.get('/admin/logs/stats', { params });
export const getLogActions = () => api.get('/admin/logs/actions');
export const getLogResourceTypes = () => api.get('/admin/logs/resource-types');

export default api;