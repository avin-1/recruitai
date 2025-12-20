import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { INTERVIEW_API_BASE } from '@/lib/apiConfig';

const InterviewCandidates = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [emailBody, setEmailBody] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const defaultEmailTemplate = (candidateName, jobTitle, company) => `Dear ${candidateName},

We are delighted to offer you the position of ${jobTitle} at ${company}!

Please find your official offer letter attached to this email.

We are excited about the possibility of you joining our team and look forward to your positive response.

Best regards,
The Recruitment Team
${company}`;

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

  const handleSelectClick = (candidateEmail) => {
    setSelectedCandidate(candidateEmail);
    // Pre-fill with default template
    setEmailBody(defaultEmailTemplate('Candidate', 'Software Engineer', 'TechCorp'));
    setSelectedFile(null);
    setIsDialogOpen(true);
  };

  const handleSendOffer = async () => {
    if (!selectedFile) {
      alert('Please select an offer letter file.');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('candidate_email', selectedCandidate);
    formData.append('offer_letter', selectedFile);
    formData.append('email_body', emailBody);

    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/send-offer`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        alert(`✓ Offer letter sent to ${selectedCandidate}`);
        setIsDialogOpen(false);
        loadCandidates(); // Refresh list
      } else {
        alert('Failed to send offer letter: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error sending offer letter: ' + err.message);
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
                            onClick={() => handleSelectClick(candidate.email)}
                            disabled={loading}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            Send Offer
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

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Send Offer Letter</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="email-body">Email Body</Label>
              <Textarea
                id="email-body"
                value={emailBody}
                onChange={(e) => setEmailBody(e.target.value)}
                rows={10}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="offer-file">Offer Letter File (PDF/Doc)</Label>
              <Input
                id="offer-file"
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSendOffer} disabled={loading}>
              {loading ? 'Sending...' : 'Send Offer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InterviewCandidates;

