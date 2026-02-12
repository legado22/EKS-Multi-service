import React from 'react'
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { 
  BookOpen, Home, ShoppingCart, LogOut, 
  Users, GraduationCap, DollarSign 
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const DashboardLayout = ({ isAdmin = false }) => {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const studentLinks = [
    { to: '/dashboard', icon: Home, label: 'Dashboard' },
    { to: '/dashboard/courses', icon: BookOpen, label: 'My Courses' },
    { to: '/dashboard/cart', icon: ShoppingCart, label: 'Cart' },
  ]

  const adminLinks = [
    { to: '/admin', icon: Home, label: 'Dashboard' },
    { to: '/admin/courses', icon: BookOpen, label: 'Courses' },
    { to: '/admin/users', icon: Users, label: 'Users' },
    { to: '/admin/orders', icon: DollarSign, label: 'Orders' },
  ]

  const links = isAdmin ? adminLinks : studentLinks

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top Bar */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <GraduationCap className="h-8 w-8 text-primary-600" />
                <span className="text-xl font-bold">Execute Tech Academy</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">{user?.full_name}</span>
              <span className="px-2 py-1 bg-primary-100 text-primary-800 rounded text-sm">
                {user?.role}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 text-gray-700 hover:text-red-600"
              >
                <LogOut className="h-5 w-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <nav className="bg-white rounded-lg shadow-md p-4">
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.to}>
                    <Link
                      to={link.to}
                      className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors"
                    >
                      <link.icon className="h-5 w-5" />
                      <span>{link.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default DashboardLayout
