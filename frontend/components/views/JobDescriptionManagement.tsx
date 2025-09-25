import React, { useState } from 'react';
import Button from '../ui/Button';
import { UploadIcon } from '../icons/UploadIcon';
import { SparklesIcon } from '../icons/SparklesIcon';

const JobDescriptionManagement: React.FC = () => {
  const [description, setDescription] = useState('');
  const [fileName, setFileName] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf') {
        setFileName(file.name);
        // Mock text extraction
        setDescription(`Extracted text from ${file.name}:\n\nWe are seeking a visionary Senior Frontend Engineer to join our dynamic team. The ideal candidate will have extensive experience in building complex, scalable, and high-performance web applications using modern frameworks like React. You will be responsible for leading the development of our user-facing products, mentoring junior engineers, and driving technical excellence within the team.`);
      } else {
        alert('Please upload a valid PDF file.');
      }
    }
  };

  const onDragOver = (e: React.DragEvent<HTMLLabelElement>) => e.preventDefault();
  
  const onDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
       if (file.type === 'application/pdf') {
        setFileName(file.name);
        // Mock text extraction
        setDescription(`Extracted text from ${file.name}:\n\n(This is a mock extraction). You will collaborate with product managers, designers, and backend engineers to create seamless and intuitive user experiences. A strong understanding of JavaScript, HTML, CSS, and component-based architecture is essential.`);
      } else {
        alert('Please upload a valid PDF file.');
      }
      e.dataTransfer.clearData();
    }
  };

  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-full max-w-3xl">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 shadow-lg">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">
            Job Description Management
          </h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Upload Job Description PDF
              </label>
              <label 
                htmlFor="jd-upload"
                className="mt-1 flex justify-center w-full px-6 pt-5 pb-6 border-2 border-slate-600 border-dashed rounded-md cursor-pointer hover:border-indigo-500"
                onDragOver={onDragOver}
                onDrop={onDrop}
              >
                <div className="space-y-1 text-center">
                  <UploadIcon className="mx-auto h-12 w-12 text-slate-400" />
                  <div className="flex text-sm text-slate-400">
                    <span className="relative rounded-md font-medium text-indigo-400 hover:text-indigo-300 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-offset-slate-800 focus-within:ring-indigo-500">
                      <span>Upload a file</span>
                      <input id="jd-upload" name="jd-upload" type="file" className="sr-only" accept=".pdf" onChange={handleFileChange} />
                    </span>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  {fileName 
                    ? <p className="text-xs text-slate-300 pt-1">File: {fileName}</p>
                    : <p className="text-xs text-slate-500">PDF format only</p>
                  }
                </div>
              </label>
            </div>
            <div>
              <label htmlFor="job-description" className="block text-sm font-medium text-gray-300 mb-2">
                Or Paste Job Description
              </label>
              <textarea
                id="job-description"
                rows={8}
                className="block w-full rounded-md border-gray-600 bg-gray-700 text-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Paste your job description here..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              ></textarea>
            </div>
            <Button
              variant="primary"
              className="w-full !text-base !py-3 flex items-center justify-center"
              onClick={() => alert('AI Profile Generation Coming Soon!')}
            >
              <SparklesIcon className="h-5 w-5 mr-2"/>
              Create AI-Enhanced Profile
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDescriptionManagement;