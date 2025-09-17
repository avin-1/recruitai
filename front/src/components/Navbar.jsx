import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <header className="bg-blue-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-8 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          <Link to="/">RecruitAI Dashboard</Link>
        </h1>
        <nav>
          <ul className="flex space-x-8 text-sm font-medium">
            <li>
              <Link to="/" className="hover:underline">
                Home
              </Link>
            </li>
            <li>
              <Link to="/profiles" className="hover:underline">
                Profiles
              </Link>
            </li>
            <li>
              <Link to="/settings" className="hover:underline">
                Settings
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
