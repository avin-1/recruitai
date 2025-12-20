import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { X } from 'lucide-react';

const Sidebar = ({ isOpen, onClose }) => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const menuItems = [
    { path: '/create-job-profile', label: 'Create Job Profile', icon: '📄' },
    { path: '/profiles', label: 'View Profiles', icon: '📂' },
    { path: '/jobs', label: 'Job Portal', icon: '💼' },
    { path: '/applicants', label: 'Applicants', icon: '👥' },
    { path: '/hr-tests', label: 'Test Manager', icon: '🧪' },
    { path: '/interviews', label: 'Interview Scheduler', icon: '📅' },
    { path: '/interview-candidates', label: 'Interview Candidates', icon: '✅' },
    { path: '/analytics', label: 'Analytics', icon: '📊' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className={`fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        onClick={onClose}
      />

      {/* Sidebar Container */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-72 bg-white/80 backdrop-blur-xl border-r border-white/50 shadow-xl
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col h-full
      `}>
        <div className="p-6 flex items-center justify-between lg:hidden">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Menu</span>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-4 flex-1 overflow-y-auto">
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-4 px-4 hidden lg:block">
            Main Menu
          </h2>
          <ul className="space-y-1">
            {menuItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={() => onClose && window.innerWidth < 1024 && onClose()}
                  className={`
                    flex items-center px-4 py-3 rounded-xl text-sm font-medium
                    transition-all duration-200 group relative
                    ${isActive(item.path)
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30'
                      : 'text-gray-600 hover:bg-white hover:shadow-md hover:text-blue-600'
                    }
                  `}
                >
                  <span className={`mr-3 text-lg transition-transform duration-200 ${isActive(item.path) ? 'scale-110' : 'group-hover:scale-110'}`}>
                    {item.icon}
                  </span>
                  <span className="flex-1">{item.label}</span>
                  {isActive(item.path) && (
                    <span className="absolute right-2 w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* User Profile Summary (Optional) */}
        <div className="p-4 border-t border-gray-100 bg-white/50">
          <div className="flex items-center space-x-3 px-2 py-2 rounded-xl hover:bg-white/80 transition-colors cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
              HR
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">HR Manager</p>
              <p className="text-xs text-gray-500 truncate">admin@recruitai.com</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
