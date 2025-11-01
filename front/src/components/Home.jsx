import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <main className="flex-1 p-12">
      <div className="bg-white shadow-lg rounded-lg p-10 max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-gray-800">
          Welcome, HR Manager!
        </h2>
        <p className="text-gray-600 mb-6 text-lg">
          What would you like to do today?
        </p>
        <div className="flex space-x-4">
          <Link to="/upload" className="bg-blue-600 text-white px-8 py-3 rounded-lg shadow-md hover:bg-blue-700 transition text-lg">
            Upload a File
          </Link>
          <Link to="/profiles" className="bg-gray-200 text-gray-800 px-8 py-3 rounded-lg shadow-md hover:bg-gray-300 transition text-lg">
            View Profiles
          </Link>
        </div>
      </div>
    </main>
  );
};

export default Home;
