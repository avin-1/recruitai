import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Bell, Search } from 'lucide-react';

const Navbar = ({ onMenuClick }) => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <header className="sticky top-0 z-40 bg-white/70 backdrop-blur-xl border-b border-white/50 shadow-sm">
      <div className="max-w-[1920px] mx-auto px-4 lg:px-8 py-3">
        <div className="flex justify-between items-center">
          {/* Left Section: Logo & Mobile Menu */}
          <div className="flex items-center space-x-4">
            <button
              onClick={onMenuClick}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
            >
              <Menu size={24} />
            </button>

            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all duration-300 group-hover:scale-105">
                <span className="text-white text-xl font-bold">R</span>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  RecruitAI
                </h1>
                <p className="text-[10px] text-gray-500 font-medium tracking-wider uppercase">Intelligent Hiring</p>
              </div>
            </Link>
          </div>

          {/* Center Section: Search (Hidden on mobile) */}
          <div className="hidden md:flex flex-1 max-w-md mx-8">
            <div className="relative w-full group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search size={18} className="text-gray-400 group-focus-within:text-blue-500 transition-colors" />
              </div>
              <input
                type="text"
                placeholder="Search candidates, jobs..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-xl leading-5 bg-gray-50/50 text-gray-900 placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-200 sm:text-sm"
              />
            </div>
          </div>

          {/* Right Section: Navigation & Profile */}
          <nav className="flex items-center space-x-2 lg:space-x-4">
            <div className="hidden md:flex items-center space-x-1">
              {[
                { path: '/', label: 'Home', icon: '🏠' },
                { path: '/profiles', label: 'Profiles', icon: '📂' },
              ].map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${isActive(item.path)
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            <div className="h-6 w-px bg-gray-200 hidden md:block"></div>

            <button className="p-2 rounded-full text-gray-500 hover:bg-gray-100 hover:text-blue-600 transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>

            <Link to="/settings" className="flex items-center space-x-2 pl-2">
              <div className="w-9 h-9 rounded-full bg-gray-100 border border-gray-200 overflow-hidden hover:ring-2 hover:ring-blue-500/20 transition-all">
                <img
                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=Felix`}
                  alt="User"
                  className="w-full h-full object-cover"
                />
              </div>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
