import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8080';

const Applicants = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [limit, setLimit] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobDetail, setJobDetail] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const loadCounts = async () => {
    setError('');
    try {
      const res = await axios.get(`${API_BASE}/jobs_counts`);
      setJobs(res.data.jobs || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  const loadApplications = async (jobId, topN) => {
    if (!jobId) return;
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.append('job_id', jobId);
      if (topN) params.append('limit', String(topN));
      const res = await axios.get(`${API_BASE}/applications?${params.toString()}`);
      setApplications(res.data.applications || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCounts(); }, []);

  const loadJobDetail = async (jobId) => {
    try {
      const res = await axios.get(`${API_BASE}/job`, { params: { job_id: jobId } });
      setJobDetail(res.data.job || null);
    } catch (err) {
      // Non-blocking; show inline error if desired
    }
  };

  const onSelectJob = (job) => {
    setSelectedJob(job);
    setApplications([]);
    setLimit('');
    loadApplications(job._id);
    loadJobDetail(job._id);
    setDetailOpen(true);
  };

  const onFilterTop = () => {
    const n = parseInt(limit, 10);
    if (!selectedJob || !n || n <= 0) return;
    loadApplications(selectedJob._id, n);
  };

  const onModifyJD = () => {
    // Navigate HR to Profiles page to modify JD there (reuse existing flow)
    window.location.href = '/profiles';
  };

  return (
    <div className="w-full p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Applicants</h2>
        <button onClick={loadCounts} className="px-3 py-2 border rounded-lg">Refresh</button>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {jobs.map(job => (
          <button
            key={job._id}
            onClick={() => onSelectJob(job)}
            className={`text-left p-4 rounded-xl border shadow-sm hover:shadow-md transition ${selectedJob?._id === job._id ? 'border-blue-600' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{job.job_title}</h3>
                <p className="text-gray-600 text-sm">{job.company} • {job.location || 'Remote'}</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-blue-600">{job.applicants_count}</p>
                <p className="text-gray-500 text-xs">Applicants</p>
              </div>
            </div>
          </button>
        ))}
        {jobs.length === 0 && <p className="text-gray-600">No approved jobs available.</p>}
      </div>

      {selectedJob && (
        <div className="bg-white border rounded-xl shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold">{selectedJob.job_title} — Applicants</h3>
            <div className="flex items-center gap-3">
              <input value={limit} onChange={(e) => setLimit(e.target.value)} placeholder="Top N" className="border rounded-lg px-3 py-2 w-28" />
              <button onClick={onFilterTop} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Filter Top</button>
              <button onClick={onModifyJD} className="px-4 py-2 border rounded-lg">Modify JD</button>
            </div>
          </div>
          {loading && <p className="text-gray-600">Loading applications…</p>}
          {!loading && (
            <div className="divide-y">
              {applications.map(app => (
                <div key={app._id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{app.name}</p>
                    <p className="text-gray-600 text-sm">{app.email}</p>
                  </div>
                  <div className="text-gray-500 text-sm">{app.resume_filename}</div>
                </div>
              ))}
              {applications.length === 0 && <p className="text-gray-600">No applications yet.</p>}
            </div>
          )}
        </div>
      )}

      {detailOpen && jobDetail && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setDetailOpen(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-semibold">{jobDetail.job_title || jobDetail.title}</h4>
              <button onClick={() => setDetailOpen(false)} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-800">
              <div>
                <p><span className="text-gray-500">Company:</span> {jobDetail.company || '—'}</p>
                <p><span className="text-gray-500">Location:</span> {jobDetail.location || '—'}</p>
                <p><span className="text-gray-500">Experience:</span> {jobDetail.experience_level || '—'}</p>
              </div>
              <div>
                <p><span className="text-gray-500">Education:</span> {jobDetail.educational_requirements || '—'}</p>
                <p><span className="text-gray-500">Approved:</span> {String(jobDetail.approved)}</p>
              </div>
            </div>
            <div className="mt-6">
              <h5 className="font-semibold">Responsibilities</h5>
              <p className="text-gray-700 whitespace-pre-line mt-1">{jobDetail.responsibilities || '—'}</p>
            </div>
            <div className="mt-4">
              <h5 className="font-semibold">Required Skills</h5>
              <p className="text-gray-700 whitespace-pre-line mt-1">{jobDetail.required_skills || '—'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Applicants;


