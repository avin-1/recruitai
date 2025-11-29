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
  AlertCircle
} from 'lucide-react';
import { SHORTLISTING_API_BASE } from '@/lib/apiConfig';

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
  
  // Filters
  const [filters, setFilters] = useState({
    difficulty_min: '',
    difficulty_max: '',
    tags: []
  });

  const availableTags = [
    'implementation', 'math', 'greedy', 'dp', 'data structures',
    'brute force', 'constructive algorithms', 'graphs', 'sortings',
    'binary search', 'dfs and similar', 'trees', 'strings', 'number theory',
    'geometry', 'combinatorics', 'two pointers', 'bitmasks', 'hashing'
  ];

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tests`);
      const data = await response.json();
      if (data.success) {
        setTests(data.tests);
        // Cache platform types - handle both object and array formats
        // Default to 'codeforces' if not specified
        const platformMap = {};
        data.tests.forEach(test => {
          const testId = test.id || test[0];
          // Default to 'codeforces' if platform_type is missing, null, undefined, or empty
          const platformType = test.platform_type || test[4] || 'codeforces';
          platformMap[testId] = platformType;
        });
        setTestPlatforms(platformMap);
        console.log('Platforms map:', platformMap); // Debug log
      }
    } catch (error) {
      console.error('Error loading tests:', error);
    }
  };

  const isCodeforcesTest = (testId) => {
    // Default to true (show buttons) if platform is not explicitly 'custom'
    const platformType = testPlatforms[testId];
    console.log(`Test ${testId} platform:`, platformType); // Debug log
    return platformType !== 'custom';
  };

  const deleteTest = async (testId) => {
    if (!confirm('Are you sure you want to delete (archive) this test?')) return;
    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}`, { method: 'DELETE' });
      const data = await response.json();
      if (data.success) {
        // Refresh list
        await loadTests();
      } else {
        alert('Failed to delete test: ' + data.error);
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
      const response = await fetch(`${API_BASE_URL}/tests/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_name: testForm.test_name,
          test_description: testForm.test_description,
          questions: testForm.platform_type === 'codeforces' ? selectedProblems : [],
          platform_type: testForm.platform_type,
          custom_platform_name: testForm.platform_type === 'custom' ? testForm.custom_platform_name : null
        })
      });

      const data = await response.json();
      if (data.success) {
        alert('Test created successfully!');
        setTestForm({ test_name: '', test_description: '', difficulty_min: '', difficulty_max: '', tags: [], platform_type: 'codeforces', custom_platform_name: '' });
        setSelectedProblems([]);
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
    // Only fetch results for Codeforces tests
    if (!isCodeforcesTest(testId)) {
      alert('Results fetching is only available for Codeforces tests.');
      return;
    }

    setLoading(true);
    try {
      // Fetch results from Codeforces API
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
        console.error('Fetch results error:', fetchData);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
      alert(`Network error: ${error.message}\n\nPlease ensure the backend server is running on port 5001.`);
    } finally {
      setLoading(false);
    }
  };

  const fetchTestResults = async (testId) => {
    // Only fetch results for Codeforces tests
    if (!isCodeforcesTest(testId)) {
      alert('Results viewing is only available for Codeforces tests.');
      return;
    }

    setLoading(true);
    try {
      // First fetch results from Codeforces if needed
      const fetchResponse = await fetch(`${API_BASE_URL}/tests/${testId}/fetch-results`, {
        method: 'POST'
      });
      
      const fetchData = await fetchResponse.json();
      if (!fetchData.success) {
        alert('Error fetching results: ' + fetchData.error);
        return;
      }

      // Then get the results
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

  const handleRemove = (email) => {
    setRemovedEmails(prev => [...prev, email]);
    setTestResults(prev => prev.filter(r => r.email !== email));
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
      // Use the bulk analysis endpoint
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/candidate-analysis`);
      const data = await response.json();
      
      if (data.success) {
        // Find the analysis for this specific candidate
        const candidateAnalysis = data.analyses.find(analysis => 
          analysis.candidate_info.username === candidate.username
        );
        
        if (candidateAnalysis) {
          setCandidateAnalysis(candidateAnalysis);
          setShowAnalysisModal(true);
        } else {
          alert('Analysis not found for this candidate');
        }
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

        <TabsContent value="create" className="space-y-6">
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
                    onChange={(e) => setTestForm({...testForm, test_name: e.target.value})}
                    placeholder="Enter test name"
                  />
                </div>
                <div>
                  <Label htmlFor="test_description">Description</Label>
                  <Textarea
                    id="test_description"
                    value={testForm.test_description}
                    onChange={(e) => setTestForm({...testForm, test_description: e.target.value})}
                    placeholder="Enter test description"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="platform_type">Test Platform</Label>
                <Select
                  value={testForm.platform_type}
                  onValueChange={(value) => {
                    setTestForm({...testForm, platform_type: value, custom_platform_name: ''});
                    setSelectedProblems([]);
                  }}
                >
                  <SelectTrigger id="platform_type">
                    <SelectValue placeholder="Select platform" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="codeforces">Codeforces</SelectItem>
                    <SelectItem value="custom">Custom Platform</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {testForm.platform_type === 'custom' && (
                <div>
                  <Label htmlFor="custom_platform_name">Custom Platform Name</Label>
                  <Input
                    id="custom_platform_name"
                    value={testForm.custom_platform_name}
                    onChange={(e) => setTestForm({...testForm, custom_platform_name: e.target.value})}
                    placeholder="e.g., LeetCode, HackerRank, Your Platform"
                  />
                </div>
              )}

              {testForm.platform_type === 'codeforces' && (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="difficulty_min">Min Difficulty</Label>
                      <Input
                        id="difficulty_min"
                        type="number"
                        value={filters.difficulty_min}
                        onChange={(e) => setFilters({...filters, difficulty_min: e.target.value})}
                        placeholder="800"
                      />
                    </div>
                    <div>
                      <Label htmlFor="difficulty_max">Max Difficulty</Label>
                      <Input
                        id="difficulty_max"
                        type="number"
                        value={filters.difficulty_max}
                        onChange={(e) => setFilters({...filters, difficulty_max: e.target.value})}
                        placeholder="2000"
                      />
                    </div>
                    <div className="flex items-end">
                      <Button onClick={fetchProblems} disabled={loading} className="w-full">
                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Fetch Problems'}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label>Tags (Optional)</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {availableTags.map(tag => (
                        <div key={tag} className="flex items-center space-x-2">
                          <Checkbox
                            id={tag}
                            checked={filters.tags.includes(tag)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setFilters({...filters, tags: [...filters.tags, tag]});
                              } else {
                                setFilters({...filters, tags: filters.tags.filter(t => t !== tag)});
                              }
                            }}
                          />
                          <Label htmlFor={tag} className="text-sm">{tag}</Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {testForm.platform_type === 'custom' && (
                <Alert>
                  <AlertDescription>
                    You've selected a custom platform. Test creation will proceed without Codeforces-specific features.
                    Candidates will receive the test link but results tracking will be handled externally.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {testForm.platform_type === 'codeforces' && problems.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Available Problems ({problems.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto">
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
                          <span className="font-mono text-sm">
                            {formatProblemId(problem)}
                          </span>
                          {problem.rating && (
                            <Badge className={getDifficultyColor(problem.rating)}>
                              {problem.rating}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{problem.name}</p>
                        {problem.tags && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {problem.tags.slice(0, 3).map(tag => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {testForm.platform_type === 'codeforces' && selectedProblems.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Selected Problems ({selectedProblems.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {selectedProblems.map((problem, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="font-mono text-sm">{formatProblemId(problem)}</span>
                      <span className="text-sm text-gray-600">{problem.name}</span>
                    </div>
                  ))}
                </div>
                <Button 
                  onClick={createTest} 
                  disabled={loading || !testForm.test_name}
                  className="w-full mt-4"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Test'}
                </Button>
              </CardContent>
            </Card>
          )}

          {testForm.platform_type === 'custom' && (
            <Card>
              <CardHeader>
                <CardTitle>Custom Platform Test</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertDescription>
                    You've selected a custom platform. Test creation will proceed without Codeforces-specific features.
                    Candidates will receive the test link but results tracking will be handled externally.
                  </AlertDescription>
                </Alert>
                <Button 
                  onClick={createTest} 
                  disabled={loading || !testForm.test_name || !testForm.custom_platform_name}
                  className="w-full mt-4"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Test'}
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="manage" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Manage Tests</CardTitle>
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
                              onClick={() => sendTestInvitations(testId)}
                            >
                              <Send className="h-4 w-4 mr-1" />
                              Send Invites
                            </Button>
                            {(platformType !== 'custom') && (
                              <>
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
                              </>
                            )}
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => deleteTest(testId)}
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
              <CardTitle>Test Results</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin" />
                  <span className="ml-2">Fetching results...</span>
                </div>
              ) : testResults.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No results available. Select a Codeforces test to view results.
                  <p className="text-sm mt-2">Results are only available for Codeforces platform tests.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {testResults.map((result, index) => (
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
                            onClick={() => getCandidateAnalysis(result, testResults[0]?.testId || 1)}
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
                <Button
                  variant="outline"
                  onClick={() => setShowAnalysisModal(false)}
                >
                  Close
                </Button>
              </div>

              {/* Candidate Info */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3">Candidate Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Username</p>
                    <p className="font-medium">{candidateAnalysis.candidate_info.username}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Email</p>
                    <p className="font-medium">{candidateAnalysis.candidate_info.email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Completion Rate</p>
                    <p className="font-medium">{candidateAnalysis.candidate_info.completion_rate}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Problems Solved</p>
                    <p className="font-medium">{candidateAnalysis.candidate_info.solved_questions}/{candidateAnalysis.candidate_info.total_questions}</p>
                  </div>
                </div>
              </div>

              {/* Performance Score */}
              <div className="mb-6">
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Overall Performance Score</h3>
                    <div className="flex items-center space-x-2">
                      <Star className="h-5 w-5 text-yellow-500" />
                      <span className="text-2xl font-bold text-blue-600">
                        {candidateAnalysis.performance_score}/100
                      </span>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${candidateAnalysis.performance_score}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Target className="h-4 w-4 text-gray-600" />
                    <span className="text-sm text-gray-600">
                      Performance Level: <span className="font-semibold text-gray-900">{candidateAnalysis.performance_level}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Difficulty Analysis */}
              {candidateAnalysis.difficulty_analysis && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3">Performance by Difficulty</h3>
                  <div className="grid grid-cols-3 gap-4">
                    {Object.entries(candidateAnalysis.difficulty_analysis).map(([difficulty, stats]) => (
                      <div key={difficulty} className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium capitalize mb-2">{difficulty}</h4>
                        <div className="text-2xl font-bold text-blue-600 mb-1">
                          {stats.solved}/{stats.total}
                        </div>
                        <div className="text-sm text-gray-600">
                          {stats.percentage}% success rate
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Insights */}
              {candidateAnalysis.insights && candidateAnalysis.insights.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                    Key Insights
                  </h3>
                  <div className="space-y-2">
                    {candidateAnalysis.insights.map((insight, index) => (
                      <div key={index} className="flex items-start space-x-2 p-3 bg-green-50 rounded-lg">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-green-800">{insight}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Strengths */}
              {candidateAnalysis.strengths && candidateAnalysis.strengths.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Star className="h-5 w-5 mr-2 text-yellow-600" />
                    Strengths
                  </h3>
                  <div className="space-y-2">
                    {candidateAnalysis.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start space-x-2 p-3 bg-yellow-50 rounded-lg">
                        <Star className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-yellow-800">{strength}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Areas for Improvement */}
              {candidateAnalysis.areas_for_improvement && candidateAnalysis.areas_for_improvement.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <AlertCircle className="h-5 w-5 mr-2 text-orange-600" />
                    Areas for Improvement
                  </h3>
                  <div className="space-y-2">
                    {candidateAnalysis.areas_for_improvement.map((area, index) => (
                      <div key={index} className="flex items-start space-x-2 p-3 bg-orange-50 rounded-lg">
                        <AlertCircle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-orange-800">{area}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {candidateAnalysis.recommendations && candidateAnalysis.recommendations.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Target className="h-5 w-5 mr-2 text-blue-600" />
                    Recommendations
                  </h3>
                  <div className="space-y-2">
                    {candidateAnalysis.recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 rounded-lg">
                        <Target className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-blue-800">{recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
