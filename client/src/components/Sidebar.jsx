import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import logo from '../assets/logo.png'
import sidebarIcon from '../assets/sidebar-minimalistic-svgrepo-com.svg'
import databaseIcon from '../assets/database-svgrepo-com.svg'

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true)
  const location = useLocation()

  const toggleSidebar = () => {
    setIsOpen(!isOpen)
  }

  const navItems = [
    { path: '/', label: 'Home', icon: null },
    { path: '/database', label: 'Database', icon: databaseIcon }
  ]

  return (
    <div className="relative">
      {/* Main Sidebar */}
      <div
        className={`bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex flex-col ${
          isOpen ? 'w-64' : 'w-16'
        } overflow-hidden`}
      >
        {/* Top bar with logo and toggle */}
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'flex-col'} p-4 border-b border-gray-200`}>
          {isOpen ? (
            <>
              <img 
                src={logo} 
                alt="Logo" 
                className="h-8 transition-opacity duration-300 opacity-100"
              />
              <button
                onClick={toggleSidebar}
                className="shrink-0 w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded transition-colors"
                aria-label="Toggle sidebar"
              >
                <img 
                  src={sidebarIcon} 
                  alt="Sidebar" 
                  className="w-5 h-5"
                />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={toggleSidebar}
                className="w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded transition-colors"
                aria-label="Open sidebar"
              >
                <img 
                  src={sidebarIcon} 
                  alt="Sidebar" 
                  className="w-5 h-5"
                />
              </button>
              <img 
                src={logo} 
                alt="Logo" 
                className="h-8 w-8 object-contain mt-4"
              />
            </>
          )}
        </div>

        {/* Navigation items */}
        <nav className={`flex-1 p-4 ${isOpen ? '' : 'flex flex-col items-center'}`}>
          {isOpen ? (
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-purple-100 text-purple-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {item.icon && (
                        <img 
                          src={item.icon} 
                          alt={item.label} 
                          className="w-5 h-5"
                        />
                      )}
                      {!item.icon && (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                      )}
                      <span className="transition-opacity duration-300 opacity-100">
                        {item.label}
                      </span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          ) : (
            <ul className="space-y-4">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-purple-100 text-purple-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                      title={item.label}
                    >
                      {item.icon && (
                        <img 
                          src={item.icon} 
                          alt={item.label} 
                          className="w-5 h-5"
                        />
                      )}
                      {!item.icon && (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          )}
        </nav>
      </div>
    </div>
  )
}

