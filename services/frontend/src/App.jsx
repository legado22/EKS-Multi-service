import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

// Layouts
import MainLayout from './components/layout/MainLayout'
import DashboardLayout from './components/layout/DashboardLayout'

// Public Pages
import HomePage from './pages/public/HomePage'
import CoursesPage from './pages/public/CoursesPage'
import CourseDetailPage from './pages/public/CourseDetailPage'
import LoginPage from './pages/public/LoginPage'
import RegisterPage from './pages/public/RegisterPage'

// Student Pages
import StudentDashboard from './pages/student/StudentDashboard'
import MyCoursesPage from './pages/student/MyCoursesPage'
import CoursePlayerPage from './pages/student/CoursePlayerPage'
import CartPage from './pages/student/CartPage'
import CheckoutPage from './pages/student/CheckoutPage'

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard'
import ManageCoursesPage from './pages/admin/ManageCoursesPage'
import ManageUsersPage from './pages/admin/ManageUsersPage'
import ManageOrdersPage from './pages/admin/ManageOrdersPage'

// Protected Route Component
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { user, isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/courses" element={<CoursesPage />} />
        <Route path="/courses/:slug" element={<CourseDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Student Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboard />} />
        <Route path="courses" element={<MyCoursesPage />} />
        <Route path="courses/:courseId" element={<CoursePlayerPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
      </Route>

      {/* Admin Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireAdmin>
            <DashboardLayout isAdmin />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="courses" element={<ManageCoursesPage />} />
        <Route path="users" element={<ManageUsersPage />} />
        <Route path="orders" element={<ManageOrdersPage />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<div>404 - Page Not Found</div>} />
    </Routes>
  )
}

export default App
