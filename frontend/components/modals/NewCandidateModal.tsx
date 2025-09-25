import React, { useState, useCallback } from 'react';
import { Candidate, PipelineStage } from '../../types';
import Modal from '../ui/Modal';
import Button from '../ui/Button';
import { UploadIcon } from '../icons/UploadIcon';

interface NewCandidateModalProps {
  onClose: () => void;
  onAddCandidate: (candidateData: Omit<Candidate, 'id' | 'jobId'>) => void;
}

const NewCandidateModal: React.FC<NewCandidateModalProps> = ({ onClose, onAddCandidate }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf') {
        setResumeFile(file);
        setError('');
      } else {
        setError('Please upload a valid PDF file.');
        setResumeFile(null);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) {
      setError('Name and email are required.');
      return;
    }
    // Basic email validation
    if (!/\S+@\S+\.\S+/.test(email)) {
        setError('Please enter a valid email address.');
        return;
    }

    onAddCandidate({
      name,
      email,
      avatarUrl: `https://i.pravatar.cc/100?u=${email}`,
      matchScore: Math.floor(Math.random() * (95 - 70 + 1) + 70), // Random score
      stage: PipelineStage.APPLIED,
      resumeSummary: `A newly added candidate. Resume parsing is pending.`,
      resumeUrl: resumeFile ? URL.createObjectURL(resumeFile) : null,
    });
  };

  const onDragOver = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
  };
  
  const onDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
       if (file.type === 'application/pdf') {
        setResumeFile(file);
        setError('');
      } else {
        setError('Please upload a valid PDF file.');
        setResumeFile(null);
      }
      e.dataTransfer.clearData();
    }
  };

  return (
    <Modal title="Add New Candidate" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-300">
            Full Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 text-slate-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-300">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-md border-slate-600 bg-slate-700 text-slate-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300">
            Upload Resume (PDF)
          </label>
           <label 
             htmlFor="resume-upload"
             className="mt-1 flex justify-center w-full px-6 pt-5 pb-6 border-2 border-slate-600 border-dashed rounded-md cursor-pointer hover:border-indigo-500"
             onDragOver={onDragOver}
             onDrop={onDrop}
           >
            <div className="space-y-1 text-center">
              <UploadIcon className="mx-auto h-12 w-12 text-slate-400" />
              <div className="flex text-sm text-slate-400">
                <span className="relative rounded-md font-medium text-indigo-400 hover:text-indigo-300 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-offset-slate-800 focus-within:ring-indigo-500">
                  <span>Upload a file</span>
                  <input id="resume-upload" name="resume-upload" type="file" className="sr-only" accept=".pdf" onChange={handleFileChange} />
                </span>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-slate-500">PDF up to 10MB</p>
            </div>
           </label>
           {resumeFile && <p className="mt-2 text-sm text-slate-300">Selected file: {resumeFile.name}</p>}
        </div>
        
        {error && <p className="text-sm text-red-400">{error}</p>}
        
        <div className="pt-4 flex justify-end space-x-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" variant="primary">Add Candidate</Button>
        </div>
      </form>
    </Modal>
  );
};

export default NewCandidateModal;