import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import {
  Button
} from '@/components/ui/button';
import {
  Input
} from '@/components/ui/input';
import {
  Label
} from '@/components/ui/label';
import {
  Textarea
} from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  Checkbox
} from '@/components/ui/checkbox';
import {
  Badge
} from '@/components/ui/badge';
import {
  Alert,
  AlertDescription
} from '@/components/ui/alert';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import {
  Loader2,
  Plus,
  Send,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Brain,
  TrendingUp,
  Star,
  Target,
  AlertCircle,
  Code,
  Briefcase,
  Trash2,
  ArrowUpDown,
  Users
} from 'lucide-react';
import { SHORTLISTING_API_BASE } from '@/lib/apiConfig';
import 'katex/dist/katex.min.css';
import Latex from 'react-latex-next';

const API_BASE_URL = SHORTLISTING_API_BASE;

const HRTestManager = () => {
  const [problems, setProblems] = useState([]);
  const [selectedProblems, setSelectedProblems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tests, setTests] = useState([]);
  const [testResults, setTestResults] = useState([]);
  const [activeTab, setActiveTab] = useState('create');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [candidateAnalysis, setCandidateAnalysis] = useState(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [removedEmails, setRemovedEmails] = useState([]);
  const [testPlatforms, setTestPlatforms] = useState({}); // Cache platform types for tests
  const [reportType, setReportType] = useState('general');
  const [jobRole, setJobRole] = useState('Software Engineer');
  const [selectedTestId, setSelectedTestId] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });
  const [showCandidateList, setShowCandidateList] = useState(false);

  // Test creation form
  const [testForm, setTestForm] = useState({
    test_name: '',
    test_description: '',
    difficulty_min: '',
    difficulty_max: '',
    tags: [],
    platform_type: 'codeforces',
    custom_platform_name: ''
  });

  // State for multi-section tests
  const [sections, setSections] = useState([
    { id: 1, name: 'Aptitude', questions: [] },
    { id: 2, name: 'Technical', questions: [] }
  ]);
  const [manualQuestion, setManualQuestion] = useState({
    question: '',
    options: ['', '', '', ''],
    correct_answer: '',
    explanation: ''
  });

  // Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { role: 'system', content: 'Hello! I can help you generate test questions. Try asking "Generate 5 aptitude questions".' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    difficulty_min: '',
    difficulty_max: '',
    tags: []
  });

  // Section Handlers
  const addSection = () => {
    const newId = sections.length > 0 ? Math.max(...sections.map(s => s.id)) + 1 : 1;
    setSections([...sections, { id: newId, name: `Section ${newId}`, questions: [] }]);
  };

  const removeSection = (id) => {
    if (sections.length <= 1) { alert("At least one section is required."); return; }
    setSections(sections.filter(s => s.id !== id));
  };

  const updateSectionName = (id, name) => {
    setSections(sections.map(s => s.id === id ? { ...s, name } : s));
  };

  const addManualQuestion = (sectionId) => {
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        return { ...s, questions: [...s.questions, manualQuestion] };
      }
      return s;
    }));
    setManualQuestion({ question: '', options: ['', '', '', ''], correct_answer: '', explanation: '' });
  };

  const removeQuestion = (sectionId, qIdx) => {
    setSections(sections.map(s => {
      if (s.id === sectionId) {
        return { ...s, questions: s.questions.filter((_, i) => i !== qIdx) };
      }
      return s;
    }));
  };

  // Chat Handlers
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatInput('');
    setChatLoading(true);

    const genMatch = userMsg.match(/(?:generate|give|make|add|need|want)\s+(?:me\s+)?(\d+)?\s*(.*)\s+(?:questions?|quesitons?|qs?)/i) ||
      userMsg.match(/(\d+)\s+(.*)\s+(?:questions?|quesitons?|qs?)/i);

    const isGenerationIntent = genMatch ||
      ((userMsg.toLowerCase().includes('question') || userMsg.toLowerCase().includes('quesiton')) &&
        (userMsg.toLowerCase().includes('generate') || userMsg.toLowerCase().includes('give') || userMsg.toLowerCase().includes('add')));

    if (isGenerationIntent) {
      let count = 5;
      let topic = 'general';

      if (genMatch) {
        count = genMatch[1] ? parseInt(genMatch[1]) : 5;
        topic = genMatch[2] || userMsg;
        topic = topic.replace(/generate|give|make|add|need|want|me|questions?|quesitons?|qs?/gi, '').trim();
      } else {
        const numMatch = userMsg.match(/(\d+)/);
        if (numMatch) count = parseInt(numMatch[0]);
        topic = userMsg.replace(/generate|give|make|add|need|want|me|questions?|quesitons?|qs?|\d+/gi, '').trim();
      }

      if (!topic || topic.length < 2) topic = 'general';

      try {
        const response = await fetch(`${API_BASE_URL}/tests/generate-questions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: topic,
            count: count,
            difficulty: 'medium',
            type: 'multiple_choice'
          })
        });
        const data = await response.json();

        if (data.success) {
          setChatMessages(prev => [...prev, {
            role: 'system',
            content: `I've generated ${data.questions.length} questions about ${topic}. You can add them to your sections below.`,
            questions: data.questions
          }]);
          setChatLoading(false);
          return;
        }
      } catch (err) {
        console.error("Generation failed, falling back to agent", err);
      }
    }

    try {
      const response = await fetch(`${API_BASE_URL}/tests/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      });

      const data = await response.json();

      if (data.success) {
        setChatMessages(prev => [...prev, {
          role: 'system',
          content: data.message,
          questions: data.action === 'SHOW_GENERATED_QUESTIONS' ? data.data : null
        }]);

        if (data.action === 'OPEN_CREATE_TEST') {
          setActiveTab('create');
        } else if (data.action === 'SWITCH_TAB_MANAGE') {
          setActiveTab('manage');
        }
      } else {
        setChatMessages(prev => [...prev, { role: 'system', content: 'Sorry, I encountered an error: ' + data.error }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'system', content: 'Network error.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const addQuestionToSection = (question, sectionId) => {
    const questionWithId = {
      ...question,
      id: question.id || `q_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    setSections(sections.map(s => {
      if (s.id.toString() === sectionId.toString()) {
        return { ...s, questions: [...s.questions, questionWithId] };
      }
      return s;
    }));
  };

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tests?t=${Date.now()}`);
      const data = await response.json();
      if (data.success) {
        setTests(data.tests);
        const platformMap = {};
        data.tests.forEach(test => {
          const testId = test.id || test[0];
          const platformType = test.platform_type || test[4] || 'codeforces';
          platformMap[testId] = platformType;
        });
        setTestPlatforms(platformMap);
      }
    } catch (error) {
      console.error('Error loading tests:', error);
    }
  };

  const deleteTest = async (testId, permanent = false) => {
    const action = permanent ? 'permanently delete' : 'archive';
    const warning = permanent
      ? 'WARNING: This will permanently remove the test and ALL associated data (questions, results, candidates). This action cannot be undone.'
      : 'This will archive the test. You can restore it later (if implemented) but invites will be blocked.';

    if (!confirm(`Are you sure you want to ${action} this test?\n\n${warning}`)) return;

    try {
      const url = permanent
        ? `${API_BASE_URL}/tests/${testId}?permanent=true`
        : `${API_BASE_URL}/tests/${testId}`;

      const response = await fetch(url, { method: 'DELETE' });
      const data = await response.json();
      if (data.success) {
        setTests(prevTests => prevTests.filter(t => {
          const tId = t.id || t[0];
          return tId !== testId;
        }));
        await loadTests();
        alert(permanent ? 'Test permanently deleted' : 'Test archived');
      } else {
        alert(`Failed to ${action} test: ` + data.error);
      }
    } catch (e) {
      console.error('Error deleting test:', e);
      alert('Network error deleting test');
    }
  };

  const fetchProblems = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.difficulty_min) params.append('difficulty_min', filters.difficulty_min);
      if (filters.difficulty_max) params.append('difficulty_max', filters.difficulty_max);
      filters.tags.forEach(tag => params.append('tags', tag));

      const response = await fetch(`${API_BASE_URL}/tests/problems?${params}`);
      const data = await response.json();

      if (data.success) {
        setProblems(data.problems);
      } else {
        alert('Error fetching problems: ' + data.error);
      }
    } catch (error) {
      console.error('Error fetching problems:', error);
      alert('Error fetching problems');
    } finally {
      setLoading(false);
    }
  };

  const handleProblemSelect = (problem, checked) => {
    if (checked) {
      setSelectedProblems([...selectedProblems, problem]);
    } else {
      setSelectedProblems(selectedProblems.filter(p =>
        p.contestId !== problem.contestId || p.index !== problem.index
      ));
    }
  };

  const createTest = async () => {
    if (!testForm.test_name) {
      alert('Please provide test name');
      return;
    }

    if (testForm.platform_type === 'codeforces' && selectedProblems.length === 0) {
      alert('Please select at least one problem for Codeforces tests');
      return;
    }

    if (testForm.platform_type === 'custom' && !testForm.custom_platform_name) {
      alert('Please enter the name of your custom platform');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...testForm,
        questions: testForm.platform_type === 'codeforces' ? selectedProblems : sections
      };

      const response = await fetch(`${API_BASE_URL}/tests/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (data.success) {
        alert('Test created successfully!');
        setTestForm({
          test_name: '',
          test_description: '',
          difficulty_min: '',
          difficulty_max: '',
          tags: [],
          platform_type: 'codeforces',
          custom_platform_name: ''
        });
        setSelectedProblems([]);
        setSections([
          { id: 1, name: 'Aptitude', questions: [] },
          { id: 2, name: 'Technical', questions: [] }
        ]);
        loadTests();
        setActiveTab('manage');
      } else {
        alert('Error creating test: ' + data.error);
      }
    } catch (error) {
      console.error('Error creating test:', error);
      alert('Error creating test');
    } finally {
      setLoading(false);
    }
  };

  const sendTestInvitations = async (testId) => {
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    const testLink = `${origin}/test/${testId}`;

    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/send-invitations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_link: testLink
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(`Test invitations sent! Success: ${data.results.total_sent} emails sent`);
      } else {
        alert('Error sending invitations: ' + data.error);
      }
    } catch (error) {
      console.error('Error sending invitations:', error);
      alert('Error sending invitations');
    }
  };

  const fetchResultsFromAPI = async (testId) => {
    setLoading(true);
    try {
      const fetchResponse = await fetch(`${API_BASE_URL}/tests/${testId}/fetch-results`, {
        method: 'POST'
      });

      const fetchData = await fetchResponse.json();
      if (fetchData.success) {
        const summary = fetchData.summary || {};
        const message = summary.errors && summary.errors.length > 0
          ? `Results fetched with warnings:\n- Processed: ${summary.processed_users || 0}/${summary.total_users || 0} users\n- Errors: ${summary.errors.slice(0, 3).join('\n')}`
          : `✅ Results fetched successfully!\n- Processed: ${summary.processed_users || 0}/${summary.total_users || 0} users\n- Problems solved: ${summary.total_solved || 0}`;
        alert(message);
      } else {
        const errorMsg = fetchData.error || 'Unknown error occurred';
        alert(`Error fetching results: ${errorMsg}\n\nPlease check:\n1. Test has registered candidates\n2. Test has questions selected\n3. Candidates have valid Codeforces usernames`);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      alert(`Network error: ${error.message}\n\nPlease ensure the backend server is running on port 5001.`);
    } finally {
      setLoading(false);
    }
  };

  const fetchTestResults = async (testId) => {
    setLoading(true);
    setSelectedTestId(testId);
    try {
      const fetchResponse = await fetch(`${API_BASE_URL}/tests/${testId}/fetch-results`, {
        method: 'POST'
      });

      const fetchData = await fetchResponse.json();
      if (!fetchData.success) {
        alert('Error fetching results: ' + fetchData.error);
        return;
      }

      const resultsResponse = await fetch(`${API_BASE_URL}/tests/${testId}/results`);
      const resultsData = await resultsResponse.json();

      if (resultsData.success) {
        setTestResults(resultsData.results);
        setRemovedEmails([]);
      } else {
        alert('Error loading results: ' + resultsData.error);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      alert('Error fetching results');
    } finally {
      setLoading(false);
    }
  };

  const deleteCandidateResult = async (email) => {
    if (!confirm(`Are you sure you want to remove candidate ${email}? This will delete their results and registration.`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/tests/${selectedTestId}/candidates/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_email: email })
      });

      const data = await response.json();
      if (data.success) {
        setTestResults(prev => prev.filter(r => r.email !== email));
        alert('Candidate removed successfully');
      } else {
        alert('Failed to remove candidate: ' + data.error);
      }
    } catch (error) {
      console.error('Error removing candidate:', error);
      alert('Error removing candidate');
    }
  };

  const handleRemove = (email) => {
    deleteCandidateResult(email);
  };

  const handleSelect = async (candidate, testId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/select-candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_email: candidate.email,
          codeforces_username: candidate.username
        })
      });
      const data = await response.json();
      if (data.success) {
        alert(`Candidate selected for interview`);
      } else {
        alert(`Failed to select candidate: ${data.error}`);
      }
    } catch (e) {
      alert('Network error selecting candidate');
    }
  };

  const getCandidateAnalysis = async (candidate, testId) => {
    setAnalysisLoading(true);
    setSelectedCandidate(candidate);

    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/candidate/${candidate.id}/analysis?report_type=${reportType}&job_role=${encodeURIComponent(jobRole)}`);
      const data = await response.json();

      if (data.success) {
        setCandidateAnalysis(data.analysis);
        setShowAnalysisModal(true);
      } else {
        alert('Error fetching analysis: ' + data.error);
      }
    } catch (error) {
      console.error('Error fetching candidate analysis:', error);
      alert('Error fetching candidate analysis');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const formatProblemId = (problem) => {
    return `${problem.contestId}${problem.index}`;
  };

  const getDifficultyColor = (rating) => {
    if (rating <= 1000) return 'bg-gray-100 text-gray-800';
    if (rating <= 1200) return 'bg-green-100 text-green-800';
    if (rating <= 1400) return 'bg-blue-100 text-blue-800';
    if (rating <= 1600) return 'bg-purple-100 text-purple-800';
    if (rating <= 1800) return 'bg-yellow-100 text-yellow-800';
    if (rating <= 2000) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const sortedResults = React.useMemo(() => {
    let sortableItems = [...testResults];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        let aValue, bValue;
        if (sortConfig.key === 'marks') {
          aValue = a.total_solved;
          bValue = b.total_solved;
        } else if (sortConfig.key === 'time') {
          aValue = a.time_taken || 0;
          bValue = b.time_taken || 0;
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [testResults, sortConfig]);

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">HR Test Manager</h1>
        <p className="text-gray-600 mt-2">Manage technical assessments using Codeforces problems</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="create">Create Test</TabsTrigger>
          <TabsTrigger value="manage">Manage Tests</TabsTrigger>
          <TabsTrigger value="results">View Results</TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="space-y-6 h-[calc(100vh-200px)] flex gap-6">
          {/* Left Panel: Test Configuration */}
          <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2">
            <Card>
              <CardHeader>
                <CardTitle>Create New Test</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="test_name">Test Name</Label>
                    <Input
                      id="test_name"
                      value={testForm.test_name}
                      onChange={(e) => setTestForm({ ...testForm, test_name: e.target.value })}
                      placeholder="Enter test name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="test_description">Description</Label>
                    <Textarea
                      id="test_description"
                      value={testForm.test_description}
                      onChange={(e) => setTestForm({ ...testForm, test_description: e.target.value })}
                      placeholder="Enter test description"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="platform_type">Test Platform</Label>
                  <Select
                    value={testForm.platform_type}
                    onValueChange={(value) => {
                      setTestForm({ ...testForm, platform_type: value, custom_platform_name: '' });
                      if (value === 'codeforces') {
                        setSelectedProblems([]);
                      } else {
                        setSections([
                          { id: 1, name: 'Aptitude', questions: [] },
                          { id: 2, name: 'Technical', questions: [] }
                        ]);
                      }
                    }}
                  >
                    <SelectTrigger id="platform_type">
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="codeforces">Codeforces (Coding Only)</SelectItem>
                      <SelectItem value="custom">Custom (Multi-Section)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {testForm.platform_type === 'custom' && (
                  <div>
                    <Label htmlFor="custom_platform_name">Platform Name</Label>
                    <Input
                      id="custom_platform_name"
                      value={testForm.custom_platform_name}
                      onChange={(e) => setTestForm({ ...testForm, custom_platform_name: e.target.value })}
                      placeholder="e.g., Internal Assessment"
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Codeforces Specific UI */}
            {testForm.platform_type === 'codeforces' && (
              <Card>
                <CardHeader>
                  <CardTitle>Select Codeforces Problems</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="difficulty_min">Min Difficulty</Label>
                      <Input
                        id="difficulty_min"
                        type="number"
                        value={filters.difficulty_min}
                        onChange={(e) => setFilters({ ...filters, difficulty_min: e.target.value })}
                        placeholder="800"
                      />
                    </div>
                    <div>
                      <Label htmlFor="difficulty_max">Max Difficulty</Label>
                      <Input
                        id="difficulty_max"
                        type="number"
                        value={filters.difficulty_max}
                        onChange={(e) => setFilters({ ...filters, difficulty_max: e.target.value })}
                        placeholder="2000"
                      />
                    </div>
                    <div className="flex items-end">
                      <Button onClick={fetchProblems} disabled={loading} className="w-full">
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Fetch Problems'}
                      </Button>
                    </div>
                  </div>

                  {/* Problem List */}
                  {problems.length > 0 && (
                    <div className="space-y-2 max-h-96 overflow-y-auto border rounded p-2">
                      {problems.map((problem, index) => (
                        <div key={index} className="flex items-center space-x-4 p-3 border rounded-lg">
                          <Checkbox
                            checked={selectedProblems.some(p =>
                              p.contestId === problem.contestId && p.index === problem.index
                            )}
                            onCheckedChange={(checked) => handleProblemSelect(problem, checked)}
                          />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-sm">{formatProblemId(problem)}</span>
                              {problem.rating && (
                                <Badge className={getDifficultyColor(problem.rating)}>{problem.rating}</Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{problem.name}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <Button
                    onClick={createTest}
                    disabled={loading || !testForm.test_name || selectedProblems.length === 0}
                    className="w-full"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Codeforces Test'}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Custom Platform Multi-Section UI */}
            {testForm.platform_type === 'custom' && (
              <div className="space-y-6">
                {/* Section Management */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Test Sections</CardTitle>
                    <Button size="sm" variant="outline" onClick={addSection}>
                      <Plus className="h-4 w-4 mr-1" /> Add Section
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <Tabs defaultValue={sections[0]?.id.toString()} className="w-full">
                      <TabsList className="flex flex-wrap h-auto">
                        {sections.map(section => (
                          <TabsTrigger key={section.id} value={section.id.toString()}>
                            {section.name} ({section.questions.length})
                          </TabsTrigger>
                        ))}
                      </TabsList>

                      {sections.map(section => (
                        <TabsContent key={section.id} value={section.id.toString()} className="space-y-4">
                          <div className="flex items-center gap-2 mb-4">
                            <Input
                              value={section.name}
                              onChange={(e) => updateSectionName(section.id, e.target.value)}
                              className="max-w-xs font-semibold"
                            />
                            <Button variant="ghost" size="sm" className="text-red-500" onClick={() => removeSection(section.id)}>
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>

                          {/* Questions List */}
                          <div className="space-y-3">
                            {section.questions.length === 0 ? (
                              <div className="text-center p-8 border-2 border-dashed rounded-lg text-gray-400">
                                No questions in this section yet. Add manually or ask AI.
                              </div>
                            ) : (
                              section.questions.map((q, qIdx) => (
                                <Card key={qIdx} className="bg-gray-50">
                                  <CardContent className="p-4 relative">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="absolute top-2 right-2 text-red-400 hover:text-red-600"
                                      onClick={() => removeQuestion(section.id, qIdx)}
                                    >
                                      <XCircle className="h-4 w-4" />
                                    </Button>
                                    <p className="font-medium mb-2">{qIdx + 1}. <Latex>{q.question}</Latex></p>
                                    {q.type === 'codeforces' ? (
                                      <div className="text-sm text-blue-600">
                                        Codeforces Problem: <a href={q.problem_link} target="_blank" rel="noopener noreferrer" className="underline">{q.data.name}</a>
                                      </div>
                                    ) : (
                                      <div className="grid grid-cols-2 gap-2 text-sm">
                                        {q.options.map((opt, oIdx) => (
                                          <div key={oIdx} className={`p-2 rounded ${opt === q.correct_answer ? 'bg-green-100 border-green-200 border' : 'bg-white border'}`}>
                                            <Latex>{opt}</Latex>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </CardContent>
                                </Card>
                              ))
                            )}
                          </div>

                          {/* Manual Question Add */}
                          <div className="mt-4 p-4 border rounded-lg bg-white">
                            <h4 className="font-medium mb-3 text-sm text-gray-700">Add Manual Question</h4>
                            <div className="space-y-3">
                              <Input
                                placeholder="Question text"
                                value={manualQuestion.question}
                                onChange={e => setManualQuestion({ ...manualQuestion, question: e.target.value })}
                              />
                              <div className="grid grid-cols-2 gap-2">
                                {manualQuestion.options.map((opt, idx) => (
                                  <Input
                                    key={idx}
                                    placeholder={`Option ${idx + 1}`}
                                    value={opt}
                                    onChange={e => {
                                      const newOpts = [...manualQuestion.options];
                                      newOpts[idx] = e.target.value;
                                      setManualQuestion({ ...manualQuestion, options: newOpts });
                                    }}
                                  />
                                ))}
                              </div>
                              <Select
                                value={manualQuestion.correct_answer}
                                onValueChange={val => setManualQuestion({ ...manualQuestion, correct_answer: val })}
                              >
                                <SelectTrigger>
                                  <SelectValue placeholder="Select Correct Answer" />
                                </SelectTrigger>
                                <SelectContent>
                                  {manualQuestion.options.map((opt, idx) => (
                                    opt && <SelectItem key={idx} value={opt}>{opt}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Button onClick={() => addManualQuestion(section.id)} disabled={!manualQuestion.question || !manualQuestion.correct_answer}>
                                <Plus className="h-4 w-4 mr-1" /> Add Question
                              </Button>
                            </div>
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  </CardContent>
                </Card>

                <Button
                  onClick={createTest}
                  disabled={loading || !testForm.test_name || sections.every(s => s.questions.length === 0)}
                  className="w-full py-6 text-lg"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Custom Test'}
                </Button>

                {/* Codeforces Integration for Custom Tests */}
                <Card className="border-t-4 border-t-purple-500">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-purple-600" />
                      Add Codeforces Problems
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="cf_min">Min Rating</Label>
                        <Input
                          id="cf_min"
                          type="number"
                          value={filters.difficulty_min}
                          onChange={(e) => setFilters({ ...filters, difficulty_min: e.target.value })}
                          placeholder="800"
                        />
                      </div>
                      <div>
                        <Label htmlFor="cf_max">Max Rating</Label>
                        <Input
                          id="cf_max"
                          type="number"
                          value={filters.difficulty_max}
                          onChange={(e) => setFilters({ ...filters, difficulty_max: e.target.value })}
                          placeholder="2000"
                        />
                      </div>
                      <div className="flex items-end">
                        <Button onClick={fetchProblems} disabled={loading} variant="secondary" className="w-full">
                          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search Problems'}
                        </Button>
                      </div>
                    </div>

                    {problems.length > 0 && (
                      <div className="space-y-2 max-h-80 overflow-y-auto border rounded p-2 bg-gray-50">
                        {problems.map((problem, index) => (
                          <div key={index} className="flex items-center justify-between p-3 border rounded-lg bg-white shadow-sm">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="font-mono text-xs font-bold text-gray-500">{formatProblemId(problem)}</span>
                                <span className="font-medium text-sm">{problem.name}</span>
                                {problem.rating && (
                                  <Badge variant="outline" className={`text-xs ${getDifficultyColor(problem.rating)}`}>
                                    {problem.rating}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex gap-1 mt-1">
                                {problem.tags?.slice(0, 2).map(tag => (
                                  <span key={tag} className="text-[10px] bg-gray-100 px-1 rounded text-gray-600">{tag}</span>
                                ))}
                              </div>
                            </div>

                            <Select onValueChange={(sectionId) => {
                              const cfQuestion = {
                                type: 'codeforces',
                                question: `[Codeforces ${formatProblemId(problem)}] ${problem.name}`,
                                problem_link: `https://codeforces.com/problemset/problem/${problem.contestId}/${problem.index}`,
                                data: problem,
                                options: [],
                                correct_answer: '',
                                explanation: `Solve this problem on Codeforces: ${problem.name}`
                              };
                              addQuestionToSection(cfQuestion, sectionId);
                            }}>
                              <SelectTrigger className="h-8 w-32 text-xs">
                                <SelectValue placeholder="Add to..." />
                              </SelectTrigger>
                              <SelectContent>
                                {sections.map(s => (
                                  <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Right Panel: AI Chat Sidebar */}
          {testForm.platform_type === 'custom' && (
            <div className="w-96 flex flex-col h-full">
              <Card className="flex-1 flex flex-col h-full border-l-4 border-l-blue-500 shadow-xl">
                <CardHeader className="bg-blue-50 py-3">
                  <CardTitle className="flex items-center gap-2 text-blue-700">
                    <Brain className="h-5 w-5" /> AI Question Generator
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
                    {chatMessages.map((msg, idx) => (
                      <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div className={`max-w-[90%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border shadow-sm rounded-bl-none'
                          }`}>
                          {msg.content}
                        </div>

                        {/* Render Generated Questions */}
                        {msg.questions && (
                          <div className="mt-2 w-full space-y-2">
                            {msg.questions.map((q, qIdx) => (
                              <div key={qIdx} className="bg-white border rounded-lg p-3 shadow-sm text-xs">
                                <p className="font-medium mb-1"><Latex>{q.question}</Latex></p>
                                <div className="flex justify-end mt-2">
                                  <Select onValueChange={(sectionId) => addQuestionToSection(q, sectionId)}>
                                    <SelectTrigger className="h-7 text-xs w-32">
                                      <SelectValue placeholder="Add to..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {sections.map(s => (
                                        <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex items-center gap-2 text-gray-400 text-sm p-2">
                        <Loader2 className="h-4 w-4 animate-spin" /> AI is thinking...
                      </div>
                    )}
                  </div>

                  <div className="p-3 bg-white border-t">
                    <form onSubmit={handleChatSubmit} className="flex gap-2">
                      <Input
                        value={chatInput}
                        onChange={e => setChatInput(e.target.value)}
                        placeholder="e.g., '5 hard python questions'"
                        className="flex-1"
                      />
                      <Button type="submit" size="icon" disabled={chatLoading || !chatInput.trim()}>
                        <Send className="h-4 w-4" />
                      </Button>
                    </form>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
        <TabsContent value="manage" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Manage Tests</CardTitle>
                <Button variant="outline" size="sm" onClick={loadTests} disabled={loading}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh List
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Test Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Platform</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tests.map((test) => {
                    // Handle both array and object formats for backwards compatibility
                    const testId = test.id || test[0];
                    const testName = test.test_name || test[1];
                    const testDescription = test.test_description || test[2];
                    // Get platform type, defaulting to 'codeforces'
                    const platformType = test.platform_type || test[4] || testPlatforms[testId] || 'codeforces';
                    const customPlatformName = test.custom_platform_name || test[5];
                    const createdDate = test.created_date || test[6] || test[4];
                    const status = test.status || test[7] || test[5] || 'active';

                    return (
                      <TableRow key={testId}>
                        <TableCell className="font-medium">{testName}</TableCell>
                        <TableCell>{testDescription || 'No description'}</TableCell>
                        <TableCell>
                          <Badge variant={platformType === 'codeforces' ? 'default' : 'outline'}>
                            {platformType === 'codeforces' ? 'Codeforces' : (customPlatformName || 'Custom')}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {createdDate ? new Date(createdDate).toLocaleDateString() : 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={status === 'active' ? 'default' : 'secondary'}>
                            {status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              onClick={() => {
                                if (status === 'archived') {
                                  alert('This test is ended and will not send the emails');
                                  return;
                                }
                                sendTestInvitations(testId);
                              }}
                            >
                              <Send className="h-4 w-4 mr-1" />
                              Send Invites
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => fetchResultsFromAPI(testId)}
                              disabled={loading}
                            >
                              <RefreshCw className="h-4 w-4 mr-1" />
                              Fetch Results
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setActiveTab('results');
                                fetchTestResults(testId);
                              }}
                              disabled={loading}
                            >
                              <Download className="h-4 w-4 mr-1" />
                              View Results
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteTest(testId, false)}
                            >
                              Archive
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              className="bg-red-700 hover:bg-red-800"
                              onClick={() => deleteTest(testId, true)}
                            >
                              Delete
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Test Results</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant={showCandidateList ? "secondary" : "outline"}
                    size="sm"
                    onClick={() => setShowCandidateList(!showCandidateList)}
                  >
                    <Users className="h-4 w-4 mr-2" />
                    {showCandidateList ? 'Hide List' : 'Show Candidates'}
                  </Button>
                  <div className="flex items-center gap-1 mr-2">
                    <Button
                      variant={sortConfig.key === 'marks' ? 'secondary' : 'ghost'}
                      size="sm"
                      onClick={() => requestSort('marks')}
                      className="text-xs"
                    >
                      Marks {sortConfig.key === 'marks' && (sortConfig.direction === 'ascending' ? '↑' : '↓')}
                    </Button>
                    <Button
                      variant={sortConfig.key === 'time' ? 'secondary' : 'ghost'}
                      size="sm"
                      onClick={() => requestSort('time')}
                      className="text-xs"
                    >
                      Time {sortConfig.key === 'time' && (sortConfig.direction === 'ascending' ? '↑' : '↓')}
                    </Button>
                  </div>
                  <Select
                    onValueChange={(testId) => fetchTestResults(testId)}
                  >
                    <SelectTrigger className="w-[250px]">
                      <SelectValue placeholder="Select a test to view results" />
                    </SelectTrigger>
                    <SelectContent>
                      {tests.map(test => {
                        const tId = test.id || test[0];
                        const tName = test.test_name || test[1];
                        return (
                          <SelectItem key={tId} value={tId.toString()}>
                            {tName}
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-6">
                {/* Main Results List */}
                <div className={`flex-1 transition-all duration-300 ${showCandidateList ? 'w-2/3' : 'w-full'}`}>
                  {loading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin" />
                      <span className="ml-2">Fetching results...</span>
                    </div>
                  ) : testResults.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No results available. Select a test above to view results.
                      <p className="text-sm mt-2">Results are only available for Codeforces platform tests.</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {sortedResults.map((result, index) => (
                        <Card key={index}>
                          <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h3 className="font-semibold">{result.username}</h3>
                                <p className="text-sm text-gray-600">{result.email}</p>
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold text-green-600">
                                  {result.total_solved}/{result.total_questions}
                                </div>
                                <p className="text-sm text-gray-600">Problems Solved</p>
                              </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4 mb-4 text-sm bg-gray-50 p-3 rounded-lg">
                              <div>
                                <span className="text-gray-500 block">Time Taken</span>
                                <span className="font-medium">
                                  {result.time_taken ? `${Math.floor(result.time_taken / 60)}m ${result.time_taken % 60}s` : 'N/A'}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-500 block">Tab Switches</span>
                                <span className={`font-medium ${result.tab_switches > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                  {result.tab_switches || 0}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-500 block">Status</span>
                                <span className="font-medium text-blue-600">Submitted</span>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                              {Object.entries(result.questions).map(([questionId, questionData]) => (
                                <div key={questionId} className="flex items-center space-x-2 p-2 border rounded">
                                  <span className="font-mono text-xs">{questionId}</span>
                                  {questionData.solved ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  )}
                                </div>
                              ))}
                            </div>

                            <div className="mt-4 flex justify-end gap-2">
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleRemove(result.email)}
                              >
                                <Trash2 className="h-4 w-4 mr-1" />
                                Remove
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleSelect(result, tests[0]?.[0] || 1)}
                              >
                                Select
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => getCandidateAnalysis(result, selectedTestId)}
                                disabled={analysisLoading}
                              >
                                {analysisLoading ? (
                                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                                ) : (
                                  <Brain className="h-4 w-4 mr-1" />
                                )}
                                See Details
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>

                {/* Candidate List Sidebar */}
                {showCandidateList && (
                  <div className="w-1/3 border-l pl-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-lg">Candidates ({testResults.length})</h3>
                    </div>
                    <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                      {sortedResults.map((result, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex-1 min-w-0 mr-2">
                            <p className="font-medium text-sm truncate" title={result.username}>{result.username}</p>
                            <p className="text-xs text-gray-500 truncate" title={result.email}>{result.email}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="text-right mr-2">
                              <span className="text-xs font-bold text-green-600 block">{result.total_solved} Solved</span>
                              <span className="text-[10px] text-gray-400 block">
                                {result.time_taken ? `${Math.floor(result.time_taken / 60)}m` : '-'}
                              </span>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleRemove(result.email)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Performance Analysis Modal */}
      {showAnalysisModal && candidateAnalysis && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Brain className="h-6 w-6 mr-2 text-blue-600" />
                  AI Performance Analysis
                </h2>
                <div className="flex gap-2 items-center mr-4">
                  <Select value={reportType} onValueChange={setReportType}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Report Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General Report</SelectItem>
                      <SelectItem value="job_specific">Job Specific Report</SelectItem>
                    </SelectContent>
                  </Select>
                  {reportType === 'job_specific' && (
                    <Input
                      placeholder="Job Role"
                      value={jobRole}
                      onChange={(e) => setJobRole(e.target.value)}
                      className="w-[200px]"
                    />
                  )}
                  <Button
                    size="sm"
                    onClick={() => getCandidateAnalysis(selectedCandidate, selectedTestId)}
                    disabled={analysisLoading}
                  >
                    {analysisLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Regenerate'}
                  </Button>
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowAnalysisModal(false)}
                >
                  Close
                </Button>
              </div>

              {/* New Scorecard Design */}
              <div className="space-y-6">
                {/* Header Section */}
                <div className="flex items-start justify-between bg-slate-50 p-6 rounded-xl border border-slate-100">
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900">{candidateAnalysis.candidate_info.username}</h3>
                    <p className="text-slate-500">{candidateAnalysis.candidate_info.email}</p>
                    <div className="flex gap-4 mt-4">
                      <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
                        <p className="text-xs text-slate-500 uppercase font-semibold">Solved</p>
                        <p className="text-lg font-bold text-slate-900">
                          {candidateAnalysis.candidate_info.solved_questions}/{candidateAnalysis.candidate_info.total_questions}
                        </p>
                      </div>
                      <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
                        <p className="text-xs text-slate-500 uppercase font-semibold">Success Rate</p>
                        <p className="text-lg font-bold text-slate-900">
                          {candidateAnalysis.codeforces_data?.success_rate || 0}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="text-center">
                    <div className="relative inline-flex items-center justify-center">
                      <svg className="w-24 h-24 transform -rotate-90">
                        <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-200" />
                        <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-blue-600"
                          strokeDasharray={251.2}
                          strokeDashoffset={251.2 - (251.2 * (candidateAnalysis.performance_score || 0)) / 100}
                        />
                      </svg>
                      <span className="absolute text-2xl font-bold text-slate-900">{candidateAnalysis.performance_score}</span>
                    </div>
                    <p className="text-sm font-medium text-blue-600 mt-1">{candidateAnalysis.performance_level}</p>
                  </div>
                </div>

                {/* Main Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Left Column: Strengths & Weaknesses */}
                  <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                      <h4 className="text-lg font-semibold flex items-center gap-2 mb-4 text-slate-900">
                        <TrendingUp className="w-5 h-5 text-green-500" /> Key Strengths
                      </h4>
                      <ul className="space-y-3">
                        {candidateAnalysis.strengths?.map((item, i) => (
                          <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                      <h4 className="text-lg font-semibold flex items-center gap-2 mb-4 text-slate-900">
                        <AlertCircle className="w-5 h-5 text-red-500" /> Areas for Improvement
                      </h4>
                      <ul className="space-y-3">
                        {candidateAnalysis.areas_for_improvement?.map((item, i) => (
                          <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                            <XCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Right Column: Skills & Recommendation */}
                  <div className="space-y-6">
                    {/* Recommendation Alert */}
                    <div className={`p-6 rounded-xl border ${candidateAnalysis.recommendations?.[0]?.includes('Do Not') ? 'bg-red-50 border-red-200' :
                      candidateAnalysis.recommendations?.[0]?.includes('Reservations') ? 'bg-yellow-50 border-yellow-200' :
                        'bg-green-50 border-green-200'
                      }`}>
                      <h4 className="text-lg font-semibold mb-2 flex items-center gap-2">
                        <Target className="w-5 h-5" /> Recommendation
                      </h4>
                      <p className="font-medium text-lg">
                        {candidateAnalysis.recommendations?.[0] || "Review Required"}
                      </p>
                    </div>

                    {/* Technical Skills */}
                    {candidateAnalysis.structured_analysis?.technical_skills && (
                      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h4 className="text-lg font-semibold flex items-center gap-2 mb-4 text-slate-900">
                          <Code className="w-5 h-5 text-blue-500" /> Technical Skills
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(candidateAnalysis.structured_analysis.technical_skills).map(([skill, level]) => (
                            <span key={skill} className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm font-medium border border-slate-200">
                              {skill}: <span className="text-blue-600">{level}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Job Fit (if available) */}
                    {candidateAnalysis.structured_analysis?.job_fit_analysis && (
                      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h4 className="text-lg font-semibold flex items-center gap-2 mb-4 text-slate-900">
                          <Briefcase className="w-5 h-5 text-purple-500" /> Job Fit Analysis
                        </h4>
                        <div className="space-y-3 text-sm">
                          <div>
                            <p className="font-medium text-slate-900">Skills Match</p>
                            <p className="text-slate-600">{candidateAnalysis.structured_analysis.job_fit_analysis.skills_match}</p>
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">Integrity Check</p>
                            <p className="text-slate-600">{candidateAnalysis.structured_analysis.job_fit_analysis.integrity_check}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Deep Dive Section */}
                {candidateAnalysis.structured_analysis?.psychometric_profile && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Psychometric Profile */}
                    <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                      <h4 className="text-lg font-semibold mb-4 text-slate-900 flex items-center gap-2">
                        <Brain className="w-5 h-5 text-indigo-600" /> Psychometric Profile
                      </h4>
                      <div className="space-y-4">
                        {Object.entries(candidateAnalysis.structured_analysis.psychometric_profile).map(([key, value]) => (
                          <div key={key}>
                            <p className="text-xs text-slate-500 uppercase font-semibold mb-1">{key.replace(/_/g, ' ')}</p>
                            <p className="font-medium text-slate-900">{value}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Code Quality */}
                    <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                      <h4 className="text-lg font-semibold mb-4 text-slate-900 flex items-center gap-2">
                        <Code className="w-5 h-5 text-blue-600" /> Code Quality
                      </h4>
                      <div className="space-y-4">
                        {candidateAnalysis.structured_analysis.code_quality && Object.entries(candidateAnalysis.structured_analysis.code_quality).map(([key, value]) => (
                          <div key={key}>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium text-slate-700 capitalize">{key}</span>
                              <span className="text-sm font-bold text-slate-900">{value}/10</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${value * 10}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Growth Potential */}
                    <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
                      <h4 className="text-lg font-semibold mb-4 text-slate-900 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-green-600" /> Growth Potential
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <p className="text-xs text-slate-500 uppercase font-semibold mb-1">Trajectory</p>
                          <p className="font-medium text-slate-900">{candidateAnalysis.structured_analysis.growth_potential?.trajectory}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase font-semibold mb-2">Recommended Next Steps</p>
                          <ul className="space-y-2">
                            {candidateAnalysis.structured_analysis.growth_potential?.next_steps?.map((step, i) => (
                              <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 shrink-0"></div>
                                {step}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Detailed Summary */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <h4 className="text-lg font-semibold mb-4 text-slate-900">Detailed Analysis</h4>
                  <div className="prose prose-slate max-w-none text-slate-600">
                    <p>{candidateAnalysis.llm_analysis}</p>
                  </div>
                </div>
              </div>

              {/* Codeforces Data */}
              {candidateAnalysis.codeforces_data && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Brain className="h-5 w-5 mr-2 text-purple-600" />
                    Codeforces Analysis
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-purple-50 rounded-lg p-4">
                      <h4 className="font-medium text-purple-800 mb-1">Total Submissions</h4>
                      <p className="text-2xl font-bold text-purple-600">
                        {candidateAnalysis.codeforces_data.total_submissions}
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-1">Success Rate</h4>
                      <p className="text-2xl font-bold text-green-600">
                        {candidateAnalysis.codeforces_data.success_rate}%
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-1">Languages Used</h4>
                      <p className="text-sm text-blue-600">
                        {candidateAnalysis.codeforces_data.languages_used?.join(', ') || 'N/A'}
                      </p>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-4">
                      <h4 className="font-medium text-orange-800 mb-1">Avg Time</h4>
                      <p className="text-sm text-orange-600">
                        {candidateAnalysis.codeforces_data.average_time ?
                          `${(candidateAnalysis.codeforces_data.average_time / 1000).toFixed(2)}s` : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HRTestManager;
