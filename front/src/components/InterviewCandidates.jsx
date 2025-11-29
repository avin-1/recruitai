import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { INTERVIEW_API_BASE } from '@/lib/apiConfig';

const InterviewCandidates = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/candidates-with-schedules`);
      const data = await res.json();
      if (data.success) {
        setCandidates(data.candidates || []);
      } else {
        setError(data.error || 'Failed to load candidates');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (candidateEmail) => {
    if (!confirm(`Are you sure you want to select ${candidateEmail} and send an offer letter?`)) {
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/select-candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_email: candidateEmail })
      });
      const data = await res.json();
      if (data.success) {
        alert(`✓ Offer letter sent to ${candidateEmail}`);
        loadCandidates(); // Refresh list
      } else {
        alert('Failed to select candidate: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error selecting candidate: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (candidateEmail) => {
    if (!confirm(`Are you sure you want to reject ${candidateEmail}? This will remove them from the database.`)) {
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/reject-candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_email: candidateEmail })
      });
      const data = await res.json();
      if (data.success) {
        alert(`✓ Candidate ${candidateEmail} rejected and removed`);
        loadCandidates(); // Refresh list
      } else {
        alert('Failed to reject candidate: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error rejecting candidate: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status, offerSent) => {
    if (status === 'selected') {
      return <Badge className="bg-green-500">Selected</Badge>;
    } else if (status === 'rejected') {
      return <Badge className="bg-red-500">Rejected</Badge>;
    } else if (offerSent) {
      return <Badge className="bg-yellow-500">Offer Sent</Badge>;
    }
    return <Badge className="bg-gray-500">Pending</Badge>;
  };

  return (
    <div className="p-6 w-full">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Interview Candidates</CardTitle>
            <Button onClick={loadCandidates} disabled={loading} variant="outline">
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}

          {loading && candidates.length === 0 ? (
            <div className="text-center py-8">Loading candidates...</div>
          ) : candidates.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No interview candidates found.</div>
          ) : (
            <div className="space-y-4">
              {candidates.map((candidate, idx) => (
                <Card key={idx} className="border">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-lg">{candidate.email}</h3>
                          {getStatusBadge(candidate.status, candidate.offer_letter_sent)}
                        </div>
                        {candidate.codeforces_username && (
                          <p className="text-sm text-gray-600 mb-1">
                            Codeforces: {candidate.codeforces_username}
                          </p>
                        )}
                        {candidate.interview_start && (
                          <p className="text-sm text-gray-600 mb-1">
                            Interview: {new Date(candidate.interview_start).toLocaleString()} - {new Date(candidate.interview_end).toLocaleString()}
                          </p>
                        )}
                        {candidate.meeting_link && (
                          <p className="text-sm text-blue-600 mb-1">
                            Meeting: <a href={candidate.meeting_link} target="_blank" rel="noopener noreferrer" className="underline">{candidate.meeting_link}</a>
                          </p>
                        )}
                      </div>
                      <div className="flex gap-2 ml-4">
                        {candidate.status !== 'selected' && (
                          <Button
                            onClick={() => handleSelect(candidate.email)}
                            disabled={loading}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            Select
                          </Button>
                        )}
                        {candidate.status !== 'rejected' && (
                          <Button
                            onClick={() => handleReject(candidate.email)}
                            disabled={loading}
                            variant="destructive"
                          >
                            Reject
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default InterviewCandidates;

