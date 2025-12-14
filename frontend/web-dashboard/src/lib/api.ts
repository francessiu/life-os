import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Auto-attach JWT token
api.interceptors.request.use((config) => {
  const token = Cookies.get('lifeos_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Handle 401 (Unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('lifeos_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (formData: FormData) => api.post('/auth/jwt/login', formData),
  register: (data: any) => api.post('/auth/register', data),
  getMe: () => api.get('/users/me'),
};

export const goalApi = {
  getGoals: () => api.get('/gamification/goals'),
  createGoal: (data: any, decompose: boolean) => 
    api.post(`/gamification/goals?decompose=${decompose}`, data),
  updateStep: (goalId: number, stepId: number, completed: boolean) => 
    api.patch(`/gamification/goals/${goalId}/step/${stepId}`, { is_completed: completed }),
  restartSmart: () => api.post('/gamification/restart-week-smart'),
};

export const pkmApi = {
  chat: (query: string, mode: string = 'productivity') => 
    api.post('/pkm/chat', { query, limit: 3, include_sources: true }),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/pkm/ingest', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const gameApi = {
  getCharacterState: () => api.get('/gamification/character/state'),
  useToken: () => api.post('/gamification/use-token'),
};

export default api;