import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const API_BASE_URL = 'http://localhost:5002/api';

const InterviewScheduler = () => {
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hrEmail, setHrEmail] = useState('avinash.bhurke01@gmail.com');
  const [selectedMap, setSelectedMap] = useState({});

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/interviews/candidates`);
      const data = await res.json();
      if (data.success) setEmails(data.emails);
    } catch {}
  };

  const fetchAvailability = async () => {
    setLoading(true);
    try {
      console.log('Fetching availability for:', hrEmail);
      const res = await fetch(`${API_BASE_URL}/interviews/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hr_email: hrEmail })
      });
      console.log('Fetch API response object:', res);
      const data = await res.json();
      console.log('Fetch HR Availability response:', data);
      if (data.success && data.slots) {
        setAvailability(data.slots);
      } else if (data.success && data.busy) {
        setAvailability(data.busy);
      } else {
        alert('Failed to fetch availability: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error fetching HR availability: ' + err.message);
      console.error('API error:', err);
    } finally {
      setLoading(false);
    }
  };

  const proposeSlots = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/interviews/propose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ availability })
      });
      const data = await res.json();
      if (data.success) setProposals(data.proposals);
    } finally {
      setLoading(false);
    }
  };

  const scheduleSelected = async () => {
    if (!selected) {
      alert('Please select a time slot first');
      return;
    }
    console.log('Scheduling with selected slot:', selected);
    // Ask HR for a meeting link (optional); empty string means backend will create Meet
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const link = window.prompt('Enter meeting link (leave blank to auto-create Google Meet):', '');
    if (link === null) {
      // User cancelled
      return;
    }
    setLoading(true);
    try {
      const payload = {
        start: selected.start,
        end: selected.end,
        hr_email: hrEmail,
        meeting_link: link || '',
        timezone: userTimezone
      };
      console.log('Sending schedule request:', payload);
      const res = await fetch(`${API_BASE_URL}/interviews/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      console.log('Schedule response:', data);
      if (data.success) {
        alert(`✓ Scheduled ${data.scheduled.length} candidates\n✓ Calendar event created\n✓ Emails sent\nMeeting link: ${data.meeting_link || 'N/A'}`);
      } else {
        alert('Failed to schedule: ' + (data.error || 'Unknown error'));
        console.error('Schedule error:', data);
      }
    } catch (err) {
      alert('Network error: ' + err.message);
      console.error('Schedule network error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSlot = (idx) => {
    setSelectedMap(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const createEventsForSelected = async () => {
    const selectedSlots = availability.filter((_, idx) => selectedMap[idx]);
    if (selectedSlots.length === 0) { alert('Select at least one slot.'); return; }
    setLoading(true);
    try {
      // Detect user's timezone
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      for (const slot of selectedSlots) {
        const res = await fetch(`${API_BASE_URL}/interviews/create_event`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            hr_email: hrEmail,
            start: slot.start,
            end: slot.end,
            attendees: emails,
            title: 'Interview',
            timezone: userTimezone,
            create_meet: true
          })
        });
        const data = await res.json();
        if (!data.success) {
          alert('Failed to create event: ' + (data.error || 'Unknown error'));
          return;
        }
      }
      alert('Event(s) created successfully.');
    } catch (err) {
      alert('Error creating events: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 w-full">
      <Card>
        <CardHeader>
          <CardTitle>Interview Scheduler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 text-sm text-gray-700">Candidates in interview list: {emails.length}</div>
          <div className="flex gap-2 mb-4">
            <Button onClick={fetchAvailability} disabled={loading}>Fetch HR Availability (Next 5 days)</Button>
            <Button onClick={proposeSlots} disabled={loading || availability.length === 0}>Ask LLM for Proposals</Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">Availability</h3>
              <div className="space-y-2">
                {availability.map((slot, idx) => (
                  <div key={idx} className={`p-3 border rounded ${selected?.start === slot.start ? 'border-blue-500' : ''}`}>
                    <div className="flex items-center gap-3">
                      <input type="checkbox" checked={!!selectedMap[idx]} onChange={() => toggleSlot(idx)} />
                      <div className="text-sm">{slot.start} — {slot.end}</div>
                    </div>
                  </div>
                ))}
                {availability.length === 0 && <div className="text-sm text-gray-500">No availability loaded.</div>}
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Proposed Slots (LLM)</h3>
              <div className="space-y-2">
                {proposals.map((slot, idx) => (
                  <div key={idx} className={`p-3 border rounded flex items-center justify-between ${selected?.start === slot.start ? 'border-green-500' : ''}`}>
                    <div className="text-sm">{slot.start} — {slot.end}</div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => setSelected(slot)}>Select</Button>
                      <Button variant="destructive" size="sm" onClick={() => setProposals(proposals.filter((_, i) => i !== idx))}>Reject</Button>
                    </div>
                  </div>
                ))}
                {proposals.length === 0 && <div className="text-sm text-gray-500">No proposals yet.</div>}
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={scheduleSelected} disabled={!selected || loading}>Schedule Selected for All Candidates</Button>
            <Button onClick={createEventsForSelected} disabled={loading}>Create Calendar Event(s)</Button>
            <Button 
              variant="outline" 
              onClick={() => navigate('/interview-candidates')}
              className="ml-auto"
            >
              End Interview Process
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default InterviewScheduler;


