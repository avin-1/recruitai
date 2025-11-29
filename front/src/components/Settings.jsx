import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { RefreshCw, CheckCircle2, XCircle, Send, Eye, Play } from 'lucide-react';
import { SETTINGS_API_BASE } from '@/lib/apiConfig';

const Settings = () => {
  const SETTINGS_API = SETTINGS_API_BASE;
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [prompts, setPrompts] = useState({});
  const [feedbackText, setFeedbackText] = useState('');
  const [hrEmail, setHrEmail] = useState('');
  const [feedbackHistory, setFeedbackHistory] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [selectedFeedback, setSelectedFeedback] = useState(null);

  useEffect(() => {
    loadAgents();
    loadFeedbackHistory();
    loadMetrics();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      loadAgentPrompts(selectedAgent);
    }
  }, [selectedAgent]);

  const loadAgents = async () => {
    try {
      const res = await fetch(`${SETTINGS_API}/agents`);
      const data = await res.json();
      if (data.success) {
        setAgents(data.agents);
        if (data.agents.length > 0 && !selectedAgent) {
          setSelectedAgent(data.agents[0].name);
        }
      }
    } catch (err) {
      console.error('Error loading agents:', err);
      setMessage({ type: 'error', text: 'Failed to load agents' });
    }
  };

  const loadAgentPrompts = async (agentName) => {
    try {
      const res = await fetch(`${SETTINGS_API}/agents/${encodeURIComponent(agentName)}/prompts`);
      const data = await res.json();
      if (data.success) {
        setPrompts(data.prompts || {});
      }
    } catch (err) {
      console.error('Error loading prompts:', err);
      setMessage({ type: 'error', text: 'Failed to load prompts' });
    }
  };

  const loadFeedbackHistory = async () => {
    try {
      const res = await fetch(`${SETTINGS_API}/feedback`);
      const data = await res.json();
      if (data.success) {
        setFeedbackHistory(data.feedback || []);
      }
    } catch (err) {
      console.error('Error loading feedback:', err);
    }
  };

  const loadMetrics = async () => {
    try {
      const res = await fetch(`${SETTINGS_API}/monitoring/metrics`);
      const data = await res.json();
      if (data.success) {
        setMetrics(data.metrics || {});
      }
    } catch (err) {
      console.error('Error loading metrics:', err);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!selectedAgent || !feedbackText.trim()) {
      setMessage({ type: 'error', text: 'Please select an agent and provide feedback' });
      return;
    }

    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const res = await fetch(`${SETTINGS_API}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: selectedAgent,
          feedback_text: feedbackText,
          hr_email: hrEmail
        })
      });

      const data = await res.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: 'Feedback submitted successfully! LLM suggestions generated.' });
        setFeedbackText('');
        setHrEmail('');
        loadFeedbackHistory();
        
        // Show LLM suggestions in modal or alert
        if (data.llm_suggestion) {
          setSelectedFeedback({
            ...data,
            feedback_text: feedbackText,
            agent_name: selectedAgent
          });
        }
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to submit feedback' });
      }
    } catch (err) {
      console.error('Error submitting feedback:', err);
      setMessage({ type: 'error', text: 'Failed to submit feedback' });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFeedback = async (feedbackId) => {
    if (!confirm('Apply these prompt modifications to the agent?')) {
      return;
    }

    try {
      const res = await fetch(`${SETTINGS_API}/feedback/${feedbackId}/apply`, {
        method: 'POST'
      });

      const data = await res.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: `Prompt modifications applied! ${data.applied_count} prompts updated.` });
        loadAgentPrompts(selectedAgent);
        loadFeedbackHistory();
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to apply modifications' });
      }
    } catch (err) {
      console.error('Error applying feedback:', err);
      setMessage({ type: 'error', text: 'Failed to apply modifications' });
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'suggested': 'bg-blue-100 text-blue-800',
      'applied': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <main className="flex-1 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">⚙️ Agent Settings & Feedback</h1>
          <p className="text-gray-600 mt-2">Monitor agent performance and provide feedback to improve AI behavior</p>
        </div>

        {message.text && (
          <Alert className={message.type === 'error' ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}>
            <AlertDescription className={message.type === 'error' ? 'text-red-800' : 'text-green-800'}>
              {message.text}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="feedback" className="space-y-4">
          <TabsList>
            <TabsTrigger value="feedback">Submit Feedback</TabsTrigger>
            <TabsTrigger value="prompts">View Prompts</TabsTrigger>
            <TabsTrigger value="history">Feedback History</TabsTrigger>
            <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          </TabsList>

          <TabsContent value="feedback" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Submit HR Feedback</CardTitle>
                <CardDescription>
                  Provide feedback about agent behavior. The LLM will analyze your feedback and suggest prompt modifications.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="agent">Select Agent</Label>
                  <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                    <SelectTrigger id="agent">
                      <SelectValue placeholder="Select an agent" />
                    </SelectTrigger>
                    <SelectContent>
                      {agents.map((agent) => (
                        <SelectItem key={agent.name} value={agent.name}>
                          {agent.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="hrEmail">Your Email (Optional)</Label>
                  <Input
                    id="hrEmail"
                    type="email"
                    value={hrEmail}
                    onChange={(e) => setHrEmail(e.target.value)}
                    placeholder="hr@example.com"
                  />
                </div>

                <div>
                  <Label htmlFor="feedback">Feedback</Label>
                  <Textarea
                    id="feedback"
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder="Example: The agent is too strict in candidate evaluation. Please consider more contextual factors like experience level and test difficulty."
                    rows={6}
                  />
                </div>

                <Button 
                  onClick={handleSubmitFeedback} 
                  disabled={loading || !selectedAgent || !feedbackText.trim()}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit Feedback
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {selectedFeedback && (
              <Card>
                <CardHeader>
                  <CardTitle>LLM Suggestions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Agent:</Label>
                    <p className="font-semibold">{selectedFeedback.agent_name}</p>
                  </div>
                  
                  <div>
                    <Label>Your Feedback:</Label>
                    <p className="text-gray-700 whitespace-pre-wrap">{selectedFeedback.feedback_text}</p>
                  </div>
                  
                  <div>
                    <Label>LLM Analysis:</Label>
                    <div className="bg-blue-50 border border-blue-200 rounded p-4">
                      <p className="text-gray-800 whitespace-pre-wrap">{selectedFeedback.llm_suggestion}</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button onClick={() => handleApplyFeedback(selectedFeedback.feedback_id)}>
                      <Play className="h-4 w-4 mr-2" />
                      Apply Modifications
                    </Button>
                    <Button variant="outline" onClick={() => setSelectedFeedback(null)}>
                      Close
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="prompts" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Agent Prompts</CardTitle>
                <CardDescription>Current prompts used by agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Select Agent</Label>
                    <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an agent" />
                      </SelectTrigger>
                      <SelectContent>
                        {agents.map((agent) => (
                          <SelectItem key={agent.name} value={agent.name}>
                            {agent.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {Object.keys(prompts).length > 0 && (
                    <div className="space-y-4">
                      {Object.entries(prompts).map(([type, prompt]) => (
                        <div key={type} className="border rounded p-4">
                          <div className="flex items-center justify-between mb-2">
                            <Label className="font-semibold capitalize">{type} Prompt</Label>
                            <Badge>v{prompt.version}</Badge>
                          </div>
                          <div className="bg-gray-50 rounded p-3 mt-2">
                            <pre className="text-sm whitespace-pre-wrap text-gray-800">{prompt.content}</pre>
                          </div>
                          <p className="text-xs text-gray-500 mt-2">
                            Modified: {new Date(prompt.modified_at).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Feedback History</CardTitle>
                <CardDescription>All feedback submissions and their status</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Agent</TableHead>
                      <TableHead>Feedback</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {feedbackHistory.map((feedback) => (
                      <TableRow key={feedback.id}>
                        <TableCell className="font-medium">{feedback.agent_name}</TableCell>
                        <TableCell>
                          <div className="max-w-md">
                            <p className="text-sm truncate">{feedback.feedback_text.substring(0, 100)}...</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(feedback.status)}>
                            {feedback.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {new Date(feedback.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            {feedback.llm_suggestion && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  try {
                                    const modifiedPrompts = feedback.modified_prompt 
                                      ? JSON.parse(feedback.modified_prompt) 
                                      : {};
                                    setSelectedFeedback({
                                      ...feedback,
                                      modified_prompts
                                    });
                                  } catch (e) {
                                    setSelectedFeedback(feedback);
                                  }
                                }}
                              >
                                <Eye className="h-3 w-3 mr-1" />
                                View
                              </Button>
                            )}
                            {feedback.status === 'suggested' && !feedback.applied && (
                              <Button
                                size="sm"
                                onClick={() => handleApplyFeedback(feedback.id)}
                              >
                                <Play className="h-3 w-3 mr-1" />
                                Apply
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monitoring" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Agent Performance Monitoring</CardTitle>
                <CardDescription>Monitor agent performance metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(metrics).map(([agentName, metric]) => (
                    <div key={agentName} className="border rounded p-4">
                      <h3 className="font-semibold mb-2">{agentName}</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <Label className="text-xs text-gray-500">Error Rate</Label>
                          <p className="text-lg font-semibold">{(metric.error_rate * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500">Response Time</Label>
                          <p className="text-lg font-semibold">{metric.response_time.toFixed(2)}s</p>
                        </div>
                        <div>
                          <Label className="text-xs text-gray-500">Total Requests</Label>
                          <p className="text-lg font-semibold">{metric.total_requests}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <Button onClick={loadMetrics} variant="outline" className="mt-4">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Metrics
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
};

export default Settings;
