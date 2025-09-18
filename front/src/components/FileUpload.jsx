import React, { useState } from 'react';
import axios from 'axios';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('⚠️ Please select a file first!');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://localhost:8080/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        },
      });
      setMessage('✅ ' + res.data.message);
    } catch (err) {
      setMessage('❌ Upload failed: ' + err.message);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  return (
    <main className="flex-1 p-12">
      <div className="bg-white shadow-lg rounded-lg p-10 max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-gray-800">
          📄 Create Job Profile
        </h2>
        <p className="text-gray-600 mb-6 text-lg">
          Upload a Job Description PDF to generate a structured job profile.
        </p>

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center
                      ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <p className="text-gray-500">
              {file ? file.name : 'Drag and drop a file here, or click to select a file'}
            </p>
          </label>
        </div>

        {progress > 0 && (
          <div className="w-full bg-gray-200 rounded-full h-2.5 my-4">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        )}

        <button
          onClick={handleUpload}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg shadow-md hover:bg-blue-700 transition text-lg mt-6"
          disabled={!file}
        >
          Upload
        </button>

        {message && (
          <p
            className={`mt-6 text-base font-medium ${
              message.startsWith('✅')
                ? 'text-green-600'
                : message.startsWith('⚠️')
                ? 'text-yellow-600'
                : 'text-red-600'
            }`}
          >
            {message}
          </p>
        )}
      </div>
    </main>
  );
};

export default FileUpload;
