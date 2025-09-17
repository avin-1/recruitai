import React from 'react';
import { Link } from 'react-router-dom';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r shadow-sm p-6 hidden lg:block">
      <h2 className="text-lg font-semibold mb-6">Menu</h2>
      <ul className="space-y-4 text-gray-700 text-base">
        <li className="hover:text-blue-600 cursor-pointer flex items-center">
          <Link to="/upload" className="flex items-center">
            📄 <span className="ml-2">Create Job Profile</span>
          </Link>
        </li>
        <li className="hover:text-blue-600 cursor-pointer flex items-center">
          <Link to="/profiles" className="flex items-center">
            📂 <span className="ml-2">View Job Profiles</span>
          </Link>
        </li>
        <li className="hover:text-blue-600 cursor-pointer flex items-center">
          <Link to="/jobs" className="flex items-center">
            ✅ <span className="ml-2">Approved Jobs</span>
          </Link>
        </li>
        <li className="hover:text-blue-600 cursor-pointer flex items-center">
          <Link to="/settings" className="flex items-center">
            ⚙️ <span className="ml-2">Settings</span>
          </Link>
        </li>
      </ul>
    </aside>
  );
};

export default Sidebar;
