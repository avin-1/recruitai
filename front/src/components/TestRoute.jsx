import React from 'react';

const TestRoute = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-600 mb-4">
          ✅ Test Route Working!
        </h1>
        <p className="text-gray-600 mb-4">
          If you can see this, the routing is working correctly.
        </p>
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h2 className="text-xl font-semibold mb-2">Candidate Test Component</h2>
          <p className="text-gray-600">
            The candidate test component should be working now.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TestRoute;
