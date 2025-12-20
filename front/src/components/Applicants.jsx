import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { CORE_API_BASE } from '@/lib/apiConfig';

const API_BASE = CORE_API_BASE;

const Applicants = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [limit, setLimit] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobDetail, setJobDetail] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectingCandidates, setSelectingCandidates] = useState(false);
  const [selectionResult, setSelectionResult] = useState(null);
  const [fetchDropdownOpen, setFetchDropdownOpen] = useState(false);

  // New State for Refactoring
  const [activeTab, setActiveTab] = useState('selected'); // 'selected' | 'rejected'
  const [rejectedApplications, setRejectedApplications] = useState([]);

  const handleRemoveCandidate = async (candidate) => {
    // Optimistic update
    setApplications(prev => prev.filter(app => app.email !== candidate.email));
    setRejectedApplications(prev => [...prev, candidate]);

    try {
      await axios.post(`${API_BASE}/update_application_status`, {
        application_id: candidate._id,
        status: 'rejected'
      });
    } catch (err) {
      console.error("Failed to update status", err);
      // Revert on error (optional, but good practice)
    }
  };

  const handleRestoreCandidate = async (candidate) => {
    // Optimistic update
    setRejectedApplications(prev => prev.filter(app => app.email !== candidate.email));
    setApplications(prev => [...prev, candidate]);

    try {
      await axios.post(`${API_BASE}/update_application_status`, {
        application_id: candidate._id,
        status: 'selected'
      });
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

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
      const allApps = res.data.applications || [];

      // Filter based on status
      const selected = allApps.filter(app => app.status !== 'rejected');
      const rejected = allApps.filter(app => app.status === 'rejected');

      setApplications(selected);
      setRejectedApplications(rejected);
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
    setRejectedApplications([]);
    setActiveTab('selected');
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

  const onSelectCandidates = async () => {
    if (!selectedJob || applications.length === 0) return;

    setSelectingCandidates(true);
    setError('');
    setSelectionResult(null);

    try {
      // Send only the currently displayed/filtered candidates
      const candidatesToSelect = applications.map(app => ({
        name: app.name,
        email: app.email,
        score: app.score
      }));

      const res = await axios.post(`${API_BASE}/select_candidates`, {
        job_id: selectedJob._id,
        candidates: candidatesToSelect
      });

      setSelectionResult(res.data);

      // Show success message
      alert(`Selection completed!\n\nTotal selected: ${res.data.total_selected}\nSuccessful emails: ${res.data.successful_emails}\nFailed emails: ${res.data.failed_emails}`);

    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setSelectingCandidates(false);
    }
  };

  const onFetchCandidates = async (source) => {
    if (!selectedJob) return;
    setLoading(true);
    setFetchDropdownOpen(false);
    try {
      const res = await axios.post(`${API_BASE}/fetch_candidates`, {
        job_id: selectedJob._id,
        source: source
      });
      alert(`✅ ${res.data.message}`);
      // Optionally reload applications if real sync happened
      // loadApplications(selectedJob._id);
    } catch (err) {
      console.error(err);
      alert(`❌ Failed to fetch from ${source}: ${err.response?.data?.error || err.message}`);
    } finally {
      setLoading(false);
    }
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

              {/* Fetch Resumes Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setFetchDropdownOpen(!fetchDropdownOpen)}
                  className="px-4 py-2 border rounded-lg bg-white hover:bg-gray-50 flex items-center gap-2"
                >
                  Fetch Resumes ⬇️
                </button>
                {fetchDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white border rounded-xl shadow-lg z-10 animate-in fade-in zoom-in duration-200">
                    <button
                      onClick={() => onFetchCandidates('linkedin')}
                      className="w-full text-left px-4 py-3 hover:bg-blue-50 text-gray-700 hover:text-blue-700 first:rounded-t-xl"
                    >
                      From LinkedIn 💼
                    </button>
                    <button
                      onClick={() => onFetchCandidates('naukri')}
                      className="w-full text-left px-4 py-3 hover:bg-blue-50 text-gray-700 hover:text-blue-700 last:rounded-b-xl"
                    >
                      From Naukri 🇮🇳
                    </button>
                  </div>
                )}
              </div>

              <button onClick={onModifyJD} className="px-4 py-2 border rounded-lg">Modify JD</button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-4 border-b mb-4">
            <button
              className={`py-2 px-4 font-medium border-b-2 transition-colors ${activeTab === 'selected' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              onClick={() => setActiveTab('selected')}
            >
              Selected Candidates ({applications.length})
            </button>
            <button
              className={`py-2 px-4 font-medium border-b-2 transition-colors ${activeTab === 'rejected' ? 'border-red-600 text-red-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              onClick={() => setActiveTab('rejected')}
            >
              Rejected Candidates ({rejectedApplications.length})
            </button>
          </div>

          {/* Select Candidates Button (Only visible in Selected Tab) */}
          {activeTab === 'selected' && (
            <div className="mt-4 flex flex-col items-center gap-2 mb-6">
              <p className="text-sm text-gray-600 text-center">
                {applications.length > 0
                  ? `Emails will be sent to the ${applications.length} candidate${applications.length === 1 ? '' : 's'} shown below`
                  : 'No candidates to select'
                }
              </p>
              <button
                onClick={onSelectCandidates}
                disabled={selectingCandidates || applications.length === 0}
                className={`px-6 py-3 rounded-lg font-semibold text-white transition ${selectingCandidates || applications.length === 0
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700'
                  }`}
              >
                {selectingCandidates ? 'Selecting Candidates...' : `Select ${applications.length} Candidates`}
              </button>
            </div>
          )}

          {selectionResult && activeTab === 'selected' && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg mb-4">
              <h4 className="font-semibold text-green-800 mb-2">Selection Results</h4>
              <p className="text-green-700">Total selected: {selectionResult.total_selected}</p>
              <p className="text-green-700">Successful emails: {selectionResult.successful_emails}</p>
              <p className="text-green-700">Failed emails: {selectionResult.failed_emails}</p>
            </div>
          )}

          {loading && <p className="text-gray-600 py-4">Loading applications…</p>}

          {!loading && (
            <div className="divide-y">
              {(activeTab === 'selected' ? applications : rejectedApplications).map((app, idx) => (
                <div key={app._id || idx} className="py-3 flex items-center justify-between group hover:bg-gray-50 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-semibold ${activeTab === 'selected' ? 'bg-blue-50 text-blue-700' : 'bg-red-50 text-red-700'}`}>
                      {idx + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">{app.name}</p>
                      <p className="text-gray-600 text-sm">{app.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    {typeof app.score === 'number' && (
                      <span className="px-2 py-1 rounded-md bg-green-50 text-green-700 font-semibold">Score: {app.score.toFixed(1)}</span>
                    )}
                    <span className="text-gray-500">{app.resume_filename}</span>

                    {activeTab === 'selected' ? (
                      <button
                        onClick={() => handleRemoveCandidate(app)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
                        title="Move to Rejected"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M3 6h18"></path>
                          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRestoreCandidate(app)}
                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-full transition-colors"
                        title="Move to Selected"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {(activeTab === 'selected' ? applications : rejectedApplications).length === 0 && (
                <p className="text-gray-500 py-8 text-center italic">
                  No {activeTab} candidates.
                </p>
              )}
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


