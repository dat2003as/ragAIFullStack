// src/services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate session ID
const generateSessionId = () => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

// Get or create session ID
const getSessionId = () => {
  let sessionId = localStorage.getItem('sessionId');
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem('sessionId', sessionId);
  }
  return sessionId;
};

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('No response from server');
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ========== CHAT API ==========
export const chatAPI = {
  sendMessage: async (sessionId, message) => {
    const response = await api.post('/chat', {
      session_id: sessionId,
      message: message,
    });
    return response.data;
  },

  getHistory: async (sessionId) => {
    const response = await api.get(`/chat/history/${sessionId}`);
    return response.data;
  },

  clearHistory: async (sessionId) => {
    const response = await api.delete(`/chat/history/${sessionId}`);
    return response.data;
  },
};

// ========== IMAGE API ==========
export const imageAPI = {
  upload: async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);  // ✅ Add to FormData
    
    const response = await api.post(
      '/upload-image',  // ✅ No query parameters
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  delete: async (sessionId) => {
    const response = await api.delete(`/upload-image/${sessionId}`);
    return response.data;
  },
};

// ========== CSV API ==========
export const csvAPI = {
  upload: async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);  // ✅ Add to FormData
    
    const response = await api.post(
      '/upload-csv',  // ✅ No query parameters
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  uploadFromURL: async (sessionId, url) => {
    const response = await api.post('/upload-csv/url', {
      session_id: sessionId,
      url: url,
    });
    return response.data;
  },

  delete: async (sessionId) => {
    const response = await api.delete(`/upload-csv/${sessionId}`);
    return response.data;
  },
};

// ========== DOCUMENT API ==========
export const documentAPI = {
  upload: async (sessionId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);  // ✅ Add to FormData
    
    const response = await api.post(
      '/upload-document',  // ✅ No query parameters
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  getInfo: async (sessionId) => {
    const response = await api.get(`/upload-document/${sessionId}/info`);
    return response.data;
  },

  delete: async (sessionId) => {
    const response = await api.delete(`/upload-document/${sessionId}`);
    return response.data;
  },
};

// ========== HEALTH API ==========
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

// ========== UTILITY ==========
export const getCurrentSessionId = () => {
  return getSessionId();
};

export const createNewSession = () => {
  const newSessionId = generateSessionId();
  localStorage.setItem('sessionId', newSessionId);
  return newSessionId;
};

export const clearSession = () => {
  localStorage.removeItem('sessionId');
};

export default api;