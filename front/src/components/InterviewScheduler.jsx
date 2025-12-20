import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Send, Check, X } from 'lucide-react';
import { INTERVIEW_API_BASE } from '@/lib/apiConfig';

const InterviewScheduler = () => {
  const navigate = useNavigate();
  const [emails, setEmails] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [proposals, setProposals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hrEmail, setHrEmail] = useState('avinash.bhurke01@gmail.com');
  const [selectedMap, setSelectedMap] = useState({});

  // Chat state
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Hello! I can help you schedule interviews. Ask me to "suggest slots".' }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    loadCandidates();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadCandidates = async () => {
    try {
      // Fetch detailed candidate info to display in list
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/candidates-with-schedules`);
      const data = await res.json();
      if (data.success) {
        // Filter out rejected candidates if any (though API should handle this)
        const activeCandidates = (data.candidates || []).filter(c => c.status !== 'rejected');
        setEmails(activeCandidates);
      }
    } catch (err) {
      console.error("Failed to load candidates", err);
    }
  };

  const handleReject = async (candidateEmail) => {
    if (!confirm(`Are you sure you want to remove ${candidateEmail} from the interview list?`)) {
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
        // Remove from local state immediately
        setEmails(prev => prev.filter(c => (c.email || c) !== candidateEmail));
        alert(`Candidate ${candidateEmail} removed.`);
      } else {
        alert('Failed to remove candidate: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error removing candidate: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailability = async () => {
    setLoading(true);
    try {
      console.log('Fetching availability for:', hrEmail);
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hr_email: hrEmail })
      });
      const data = await res.json();
      if (data.success && data.slots) {
        setAvailability(data.slots);
      } else if (data.success && data.busy) {
        setAvailability(data.busy);
      } else {
        alert('Failed to fetch availability: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Error fetching HR availability: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const proposeSlots = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/propose`, {
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

  const scheduleSlot = async (slot) => {
    // Ask HR for a meeting link (optional); empty string means backend will create Meet
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const link = window.prompt('Enter meeting link (leave blank to auto-create Google Meet):', '');
    if (link === null) return; // User cancelled

    setLoading(true);
    try {
      const payload = {
        start: slot.start,
        end: slot.end,
        hr_email: hrEmail,
        meeting_link: link || '',
        timezone: userTimezone
      };

      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        const successMsg = `✓ Scheduled for ${data.scheduled.length} candidates. Meeting link: ${data.meeting_link || 'N/A'}`;
        alert(successMsg);
        setMessages(prev => [...prev, { role: 'system', content: successMsg }]);
      } else {
        alert('Failed to schedule: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      alert('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const scheduleSelected = async () => {
    // Determine which slots to schedule:
    // 1. If checkboxes are checked in "Availability", use those.
    // 2. If no checkboxes, check if a "Proposed Slot" is selected.
    const checkedIndices = Object.keys(selectedMap).filter(k => selectedMap[k]);
    let slotsToSchedule = [];

    if (checkedIndices.length > 0) {
      slotsToSchedule = checkedIndices.map(idx => availability[idx]);
    } else if (selected) {
      slotsToSchedule = [selected];
    }

    if (slotsToSchedule.length === 0) {
      alert('Please select at least one time slot (via checkboxes or proposal selection).');
      return;
    }

    // Ask for meeting link once for all
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const link = window.prompt(`Scheduling ${slotsToSchedule.length} slot(s). Enter meeting link (leave blank to auto-create Google Meet):`, '');
    if (link === null) return; // User cancelled

    setLoading(true);
    let successCount = 0;
    let failCount = 0;

    try {
      for (const slot of slotsToSchedule) {
        const payload = {
          start: slot.start,
          end: slot.end,
          hr_email: hrEmail,
          meeting_link: link || '',
          timezone: userTimezone
        };

        try {
          const res = await fetch(`${INTERVIEW_API_BASE}/interviews/schedule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await res.json();
          if (data.success) {
            successCount++;
          } else {
            console.error('Failed to schedule slot:', slot, data.error);
            failCount++;
          }
        } catch (err) {
          console.error('Network error scheduling slot:', slot, err);
          failCount++;
        }
      }

      const summary = `Scheduled: ${successCount}\nFailed: ${failCount}`;
      alert(summary);
      if (successCount > 0) {
        setMessages(prev => [...prev, { role: 'system', content: `✓ ${summary}` }]);
        // Clear selections
        setSelected(null);
        setSelectedMap({});
      }

    } catch (err) {
      alert('Unexpected error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleSlot = (idx) => {
    setSelectedMap(prev => ({ ...prev, [idx]: !prev[idx] }));
  };
  // createEventsForSelected removed as it is now redundant


  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMsg = inputMessage;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInputMessage('');
    setLoading(true);

    try {
      const res = await fetch(`${INTERVIEW_API_BASE}/interviews/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          hr_email: hrEmail,
          client_time: new Date().toISOString()
        })
      });
      const data = await res.json();

      if (data.success) {
        setMessages(prev => [...prev, {
          role: 'system',
          content: data.response,
          slots: data.slots
        }]);

        // Handle Agent Actions
        if (data.action === 'REMOVE_CANDIDATE' && data.data?.email) {
          // Small delay to let the message appear first
          setTimeout(() => {
            handleReject(data.data.email);
          }, 500);
        }

      } else {
        setMessages(prev => [...prev, { role: 'system', content: 'Sorry, I encountered an error.' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: 'Network error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 w-full flex flex-col lg:flex-row gap-6 h-[calc(100vh-100px)]">
      {/* Left Panel: Scheduler Controls */}
      <div className="flex-1 overflow-y-auto">
        <Card className="h-full">
          <CardHeader>
            <CardTitle>Interview Scheduler</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 text-sm text-gray-700">Candidates in interview list: {emails.length}</div>

            {/* Candidate List Section */}
            <div className="mb-6 border rounded-lg p-4 bg-gray-50">
              <h3 className="font-semibold mb-3">Candidates</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {emails.length === 0 ? (
                  <div className="text-sm text-gray-500 italic">No candidates found.</div>
                ) : (
                  emails.map((candidate, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border text-sm">
                      <span className="truncate flex-1" title={candidate.email || candidate}>{candidate.email || candidate}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0"
                        onClick={() => handleReject(candidate.email || candidate)}
                        title="Remove Candidate"
                      >
                        <X size={16} />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="flex gap-2 mb-4">
              <Button onClick={fetchAvailability} disabled={loading}>Fetch HR Availability (Next 5 days)</Button>
              <Button onClick={proposeSlots} disabled={loading || availability.length === 0}>Ask LLM for Proposals</Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold mb-2">Availability</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
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
            <div className="mt-4 flex gap-2 flex-wrap">
              <Button
                onClick={scheduleSelected}
                disabled={loading || (!selected && Object.keys(selectedMap).filter(k => selectedMap[k]).length === 0)}
              >
                Schedule Selected
              </Button>
              {/* Create Calendar Event(s) button removed */}
              <Button
                variant="outline"
                onClick={() => navigate('/interview-candidates')}
                className="ml-auto"
              >
                View All Candidates
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right Panel: Chat Interface */}
      <div className="w-full lg:w-96 flex flex-col">
        <Card className="flex-1 flex flex-col h-full">
          <CardHeader className="pb-3 border-b">
            <CardTitle className="text-lg flex items-center gap-2">
              🤖 AI Assistant
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[85%] p-3 rounded-2xl ${msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white border shadow-sm rounded-bl-none'
                    }`}>
                    <p className="text-sm">{msg.content}</p>
                  </div>

                  {/* Render slots if available in system message */}
                  {msg.slots && msg.slots.length > 0 && (
                    <div className="mt-2 space-y-2 w-full max-w-[85%]">
                      {msg.slots.map((slot, sIdx) => (
                        <div key={sIdx} className="bg-white border rounded-xl p-3 shadow-sm">
                          <div className="text-xs text-gray-500 mb-1">Proposed Slot</div>
                          <div className="text-sm font-medium mb-2">
                            {new Date(slot.start).toLocaleString()}
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              className="h-7 text-xs bg-green-600 hover:bg-green-700"
                              onClick={() => scheduleSlot(slot)}
                            >
                              <Check size={12} className="mr-1" /> Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs text-red-600 hover:bg-red-50"
                              onClick={() => {
                                // Visually remove this slot from the message (local state update)
                                const newMessages = [...messages];
                                const msgIndex = newMessages.indexOf(msg);
                                if (msgIndex !== -1) {
                                  newMessages[msgIndex].slots = newMessages[msgIndex].slots.filter((_, i) => i !== sIdx);
                                  setMessages(newMessages);
                                }
                              }}
                            >
                              <X size={12} className="mr-1" /> Disapprove
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <div className="p-3 border-t bg-white">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type 'suggest slots'..."
                  className="flex-1"
                  disabled={loading}
                />
                <Button type="submit" size="icon" disabled={loading || !inputMessage.trim()}>
                  <Send size={18} />
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InterviewScheduler;


