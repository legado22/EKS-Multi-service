import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
      toast.error('Session expired. Please login again.')
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}

// Course API
export const courseAPI = {
  getCourses: (params) => api.get('/courses', { params }),
  getCourse: (id) => api.get(`/courses/${id}`),
  getCourseBySlug: (slug) => api.get(`/courses/slug/${slug}`),
}

// Enrollment API
export const enrollmentAPI = {
  getMyEnrollments: () => api.get('/enrollments'),
  getEnrollment: (id) => api.get(`/enrollments/${id}`),
  getCourseEnrollment: (courseId) => api.get(`/courses/${courseId}/enrollment`),
  updateProgress: (progressId, data) => api.put(`/progress/${progressId}`, data),
}

// Cart API
export const cartAPI = {
  getCart: () => api.get('/cart'),
  addToCart: (courseId) => api.post('/cart/items', { course_id: courseId }),
  removeFromCart: (itemId) => api.delete(`/cart/items/${itemId}`),
  clearCart: () => api.delete('/cart'),
}

// Order API
export const orderAPI = {
  createOrder: (data) => api.post('/orders', data),
  getOrders: () => api.get('/orders'),
  getOrder: (id) => api.get(`/orders/${id}`),
}

// Payment API
export const paymentAPI = {
  initiatePayment: (data) => api.post('/payments/initiate', data),
  verifyPayment: (paymentId) => api.get(`/payments/verify/${paymentId}`),
  getPayments: () => api.get('/payments'),
}

// Admin APIs
export const adminAPI = {
  getUsers: () => api.get('/users'),
  createCourse: (data) => api.post('/courses', data),
  updateCourse: (id, data) => api.put(`/courses/${id}`, data),
  deleteCourse: (id) => api.delete(`/courses/${id}`),
  getOrders: () => api.get('/orders'),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
}

export default api
