import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { CORE_API_BASE } from '@/lib/apiConfig';

const API_BASE = CORE_API_BASE;

const JobCard = ({ job, onApply, onOpenDetail }) => {
  return (
    <div
      className="bg-white rounded-xl shadow-md border p-6 flex flex-col justify-between hover:shadow-lg transition cursor-pointer"
      onClick={() => onOpenDetail(job)}
    >
      <div>
        <h3 className="text-xl font-semibold text-gray-900">{job.job_title}</h3>
        <p className="text-gray-600 mt-1">{job.company} • {job.location || 'Remote'}</p>
        {job.summary && (
          <p className="text-gray-700 mt-3 line-clamp-3">{String(job.summary).slice(0, 180)}{String(job.summary).length > 180 ? '…' : ''}</p>
        )}
      </div>
      <div className="mt-4">
        <button onClick={(e) => { e.stopPropagation(); onApply(job); }} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Apply Now
        </button>
      </div>
    </div>
  );
};

const ApplyModal = ({ open, job, onClose, onSubmitted }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!open || !job) return null;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!resume) { setError('Please select a resume file.'); return; }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('job_id', job._id);
      formData.append('name', name);
      formData.append('email', email);
      formData.append('resume', resume);

      await axios.post(`${API_BASE}/apply`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between">
          <h4 className="text-lg font-semibold">Apply for {job.job_title}</h4>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm text-gray-700">Full Name</label>
            <input className="mt-1 w-full border rounded-lg px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-gray-700">Email</label>
            <input type="email" className="mt-1 w-full border rounded-lg px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm text-gray-700">Resume (PDF/Doc)</label>
            <input type="file" accept=".pdf,.doc,.docx" className="mt-1 w-full" onChange={(e) => setResume(e.target.files?.[0] || null)} required />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded-lg">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60">
              {loading ? 'Submitting…' : 'Submit Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const JobPortal = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [applyOpen, setApplyOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [jobDetail, setJobDetail] = useState(null);

  const loadJobs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE}/jobs`);
      setJobs(res.data.jobs || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadJobs(); }, []);

  const onApply = (job) => {
    setSelectedJob(job);
    setApplyOpen(true);
  };

  const openDetail = async (job) => {
    try {
      setSelectedJob(job);
      setDetailOpen(true);
      const res = await axios.get(`${API_BASE}/job`, { params: { job_id: job._id } });
      setJobDetail(res.data.job || null);
    } catch (err) {
      setJobDetail(null);
    }
  };

  return (
    <div className="w-full p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Open Roles</h2>
        <button onClick={loadJobs} className="px-3 py-2 border rounded-lg">Refresh</button>
      </div>
      {loading && <p className="text-gray-600">Loading jobs…</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <JobCard key={job._id} job={job} onApply={onApply} onOpenDetail={openDetail} />
          ))}
          {jobs.length === 0 && <p className="text-gray-600">No jobs available yet.</p>}
        </div>
      )}

      <ApplyModal
        open={applyOpen}
        job={selectedJob}
        onClose={() => setApplyOpen(false)}
        onSubmitted={() => setTimeout(loadJobs, 300)}
      />

      {detailOpen && selectedJob && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setDetailOpen(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-semibold">{jobDetail?.job_title || jobDetail?.title || selectedJob.job_title}</h4>
              <button onClick={() => setDetailOpen(false)} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-800">
              <div>
                <p><span className="text-gray-500">Company:</span> {jobDetail?.company ?? selectedJob.company ?? '—'}</p>
                <p><span className="text-gray-500">Location:</span> {jobDetail?.location ?? selectedJob.location ?? '—'}</p>
                <p><span className="text-gray-500">Experience:</span> {jobDetail?.experience_level ?? '—'}</p>
              </div>
              <div>
                <p><span className="text-gray-500">Education:</span> {jobDetail?.educational_requirements ?? '—'}</p>
                <p><span className="text-gray-500">Approved:</span> {String(jobDetail?.approved ?? true)}</p>
              </div>
            </div>
            <div className="mt-6">
              <h5 className="font-semibold">Responsibilities</h5>
              <p className="text-gray-700 whitespace-pre-line mt-1">{jobDetail?.responsibilities ?? '—'}</p>
            </div>
            <div className="mt-4">
              <h5 className="font-semibold">Required Skills</h5>
              <p className="text-gray-700 whitespace-pre-line mt-1">{jobDetail?.required_skills ?? '—'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobPortal;


