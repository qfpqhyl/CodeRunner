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

export default api;