import axios from 'axios';

// Get dynamic backend URL from localStorage or use default
const getBackendUrl = () => {
  const savedUrl = localStorage.getItem('backendUrl');
  if (savedUrl) {
    // Remove trailing slash if present
    return savedUrl.replace(/\/$/, '');
  }
  // Always use localhost:8000 as default, user will configure for production
  return 'http://localhost:8000';
};

const API_BASE_URL = getBackendUrl();

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请检查后端服务是否正常运行';
    } else if (error.code === 'ERR_NETWORK') {
      error.message = '无法连接到后端服务，请检查后端地址配置';
    }
    return Promise.reject(error);
  }
);

// Function to update backend URL
export const updateBackendUrl = (newUrl) => {
  localStorage.setItem('backendUrl', newUrl);
  // Update axios instance baseURL
  api.defaults.baseURL = newUrl.replace(/\/$/, '');
};

// Function to test backend connection
export const testBackendConnection = async (url) => {
  try {
    const testUrl = url.replace(/\/$/, '');
    await axios.get(`${testUrl}/`, {
      timeout: 5000,
      // Add CORS headers to handle cross-origin requests
      headers: {
        'Content-Type': 'application/json',
      },
      // Set withCredentials to false to avoid CORS issues
      withCredentials: false
    });
    return { success: true, message: '连接成功' };
  } catch (error) {
    let message = '连接失败';
    if (error.code === 'ECONNABORTED') {
      message = '连接超时';
    } else if (error.code === 'ERR_NETWORK') {
      message = '网络错误，无法访问';
    } else if (error.code === 'ECONNREFUSED') {
      message = '连接被拒绝，请检查后端服务是否启动';
    } else if (error.response?.status === 404) {
      message = '后端服务不存在，请检查地址是否正确';
    } else if (error.response?.status === 0 || error.message.includes('CORS')) {
      message = '跨域请求失败，请检查后端CORS配置';
    }
    return { success: false, message };
  }
};

// Function to get current backend URL
export const getCurrentBackendUrl = () => {
  return api.defaults.baseURL;
};

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
export const saveCodeToLibraryFromShare = (saveData) => api.post('/code-library/save', saveData);
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

// AI Configuration endpoints
export const createAIConfig = (configData) => api.post('/ai-configs', configData);
export const getAIConfigs = () => api.get('/ai-configs');
export const updateAIConfig = (configId, configData) => api.put(`/ai-configs/${configId}`, configData);
export const deleteAIConfig = (configId) => api.delete(`/ai-configs/${configId}`);
export const generateCodeByAI = (promptData) => api.post('/ai/generate-code', promptData);

// Database Import/Export endpoints (Admin only)
export const exportDatabase = () => {
  return api.post('/admin/database/export', {}, {
    responseType: 'blob'
  });
};

export const importDatabase = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/admin/database/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

export const getDatabaseInfo = () => api.get('/admin/database/info');

// Conda environments endpoint
export const getCondaEnvironments = () => api.get('/conda-environments');

// Environment management endpoints
export const getEnvironmentPackages = (envName) => api.get(`/environments/${envName}/packages`);
export const getEnvironmentInfo = (envName) => api.get(`/environments/${envName}/info`);
export const installPackage = (envName, packageName) => api.post(`/environments/${envName}/packages/install`, { package_name: packageName });
export const uninstallPackage = (envName, packageName) => api.delete(`/environments/${envName}/packages/${packageName}`);
export const upgradePackage = (envName, packageName) => api.put(`/environments/${envName}/packages/${packageName}/upgrade`);

// User environment management endpoints
export const getUserEnvironments = () => api.get('/user-environments');
export const createUserEnvironment = (envData) => api.post('/user-environments', envData);
export const getUserEnvironment = (envId) => api.get(`/user-environments/${envId}`);
export const updateUserEnvironment = (envId, envData) => api.put(`/user-environments/${envId}`, envData);
export const deleteUserEnvironment = (envId) => api.delete(`/user-environments/${envId}`);

// Admin user environment management endpoints
export const adminGetAllUserEnvironments = () => api.get('/admin/user-environments');
export const adminDeleteUserEnvironment = (envId) => api.delete(`/admin/user-environments/${envId}`);

// User Profile endpoints
export const getUserProfile = () => api.get('/profile');
export const updateUserProfile = (profileData) => api.put('/profile', profileData);
export const uploadAvatar = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/profile/upload-avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};
export const deleteAvatar = () => api.delete('/profile/avatar');
export const getAvatarUrl = (filename) => `${api.defaults.baseURL}/api/avatars/${filename}`;
export const getUserEnhancedStats = () => api.get('/profile/enhanced-stats');

// User Activity Logs endpoints
export const getUserActivityLogs = (params = {}) => api.get('/profile/logs', { params });
export const getUserLogActions = () => api.get('/profile/logs/actions');
export const getUserLogResourceTypes = () => api.get('/profile/logs/resource-types');
export const getUserProfileStats = () => api.get('/profile/stats');

// Community API endpoints
export const createPost = (postData) => api.post('/community/posts', postData);
export const getPosts = (params = {}) => api.get('/community/posts', { params });
export const getPost = (postId) => api.get(`/community/posts/${postId}`);
export const deletePost = (postId) => api.delete(`/community/posts/${postId}`);
export const likePost = (postId) => api.post(`/community/posts/${postId}/like`);
export const favoritePost = (postId) => api.post(`/community/posts/${postId}/favorite`);
export const createComment = (postId, commentData) => api.post(`/community/posts/${postId}/comments`, commentData);
export const getComments = (postId, params = {}) => api.get(`/community/posts/${postId}/comments`, { params });
export const likeComment = (commentId) => api.post(`/community/comments/${commentId}/like`);
export const followUser = (userId) => api.post(`/community/follow/${userId}`);

// Follow/Followers endpoints
export const getUserFollowers = (userId, params = {}) => api.get(`/users/${userId}/followers`, { params });
export const getUserFollowing = (userId, params = {}) => api.get(`/users/${userId}/following`, { params });
export const getFollowStatus = (userId) => api.get(`/users/${userId}/follow-status`);
export const getUserByUsername = (username) => api.get(`/users/by-username/${username}`);

// User-specific content endpoints
export const getUserPosts = (userId, params = {}) => api.get(`/users/${userId}/posts`, { params });
export const getUserCodeLibrary = (userId, params = {}) => api.get(`/users/${userId}/code-library`, { params });
export const getUserPublicStats = (userId) => api.get(`/users/${userId}/stats`);

// Code Library Save/Copy endpoints
export const getAvailableEnvironments = () => api.get('/environments/available');

export default api;