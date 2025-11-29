import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Alert, 
  AlertDescription 
} from '@/components/ui/alert';
import { 
  Badge 
} from '@/components/ui/badge';
import { 
  Loader2, 
  CheckCircle, 
  ExternalLink,
  User,
  Mail,
  Clock,
  Target,
  BookOpen,
  AlertTriangle,
  Info
} from 'lucide-react';
import { SHORTLISTING_API_BASE } from '@/lib/apiConfig';

const API_BASE_URL = SHORTLISTING_API_BASE;

const CandidateTest = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [testQuestions, setTestQuestions] = useState([]);
  const [testInfo, setTestInfo] = useState(null);
  const [registrationForm, setRegistrationForm] = useState({
    candidate_email: '',
    codeforces_username: ''
  });
  const [registrationStatus, setRegistrationStatus] = useState('pending'); // pending, success, error
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (testId) {
      loadTestInfo();
    }
  }, [testId]);

  const loadTestInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/questions`);
      const data = await response.json();
      
      if (data.success) {
        setTestQuestions(data.questions);
        setTestInfo(data.test_info);
      } else {
        setErrorMessage('Error loading test information: ' + data.error);
        setRegistrationStatus('error');
      }
    } catch (error) {
      console.error('Error loading test info:', error);
      setErrorMessage('Error loading test information');
      setRegistrationStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleRegistration = async (e) => {
    e.preventDefault();
    
    if (!registrationForm.candidate_email || !registrationForm.codeforces_username) {
      setErrorMessage('Please fill in all fields');
      setRegistrationStatus('error');
      return;
    }

    setLoading(true);
    setErrorMessage('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          candidate_email: registrationForm.candidate_email,
          codeforces_username: registrationForm.codeforces_username
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setRegistrationStatus('success');
        setSuccessMessage('Registration successful! You can now proceed with the test.');
      } else {
        setErrorMessage('Registration failed: ' + data.error);
        setRegistrationStatus('error');
      }
    } catch (error) {
      console.error('Error registering:', error);
      setErrorMessage('Registration failed. Please try again.');
      setRegistrationStatus('error');
    } finally {
      setLoading(false);
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

  const openProblemInNewTab = (problem) => {
    const url = `https://codeforces.com/problemset/problem/${problem.contestId}/${problem.index}`;
    window.open(url, '_blank');
  };

  if (loading && !testInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading test information...</p>
        </div>
      </div>
    );
  }

  if (registrationStatus === 'error' && !testInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6">
            <Alert variant="destructive">
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
            <Button 
              onClick={() => navigate('/')} 
              className="w-full mt-4"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Technical Assessment Test
            </h1>
            {testInfo && (
              <div className="space-y-2">
                <p className="text-xl text-blue-600 font-semibold">
                  {testInfo.name}
                </p>
                <p className="text-gray-600">
                  {testInfo.description}
                </p>
                <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 mt-4">
                  <div className="flex items-center space-x-1">
                    <BookOpen className="h-4 w-4" />
                    <span>{testQuestions.length} Problems</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>No Time Limit</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="h-4 w-4" />
                    <span>Auto Tracked</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {registrationStatus === 'pending' && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                <User className="h-5 w-5 mr-2" />
                Register for Test
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegistration} className="space-y-4">
                <div>
                  <Label htmlFor="candidate_email">Email Address</Label>
                  <Input
                    id="candidate_email"
                    type="email"
                    value={registrationForm.candidate_email}
                    onChange={(e) => setRegistrationForm({
                      ...registrationForm,
                      candidate_email: e.target.value
                    })}
                    placeholder="Enter your email address"
                    required
                  />
                </div>
                
                <div>
                  <Label htmlFor="codeforces_username">Codeforces Username</Label>
                  <Input
                    id="codeforces_username"
                    value={registrationForm.codeforces_username}
                    onChange={(e) => setRegistrationForm({
                      ...registrationForm,
                      codeforces_username: e.target.value
                    })}
                    placeholder="Enter your Codeforces username"
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Make sure this username exists on Codeforces
                  </p>
                </div>

                {errorMessage && (
                  <Alert variant="destructive">
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  type="submit" 
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Registering...
                    </>
                  ) : (
                    'Register for Test'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {registrationStatus === 'success' && (
          <Card className="mb-8">
            <CardContent className="p-6">
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  {successMessage}
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BookOpen className="h-5 w-5 mr-2" />
              Test Problems ({testQuestions.length})
            </CardTitle>
            <p className="text-gray-600">
              Solve the following problems on Codeforces. Your progress will be automatically tracked.
            </p>
          </CardHeader>
          <CardContent>
            {testQuestions.length > 0 ? (
              <div className="space-y-6">
                {testQuestions.map((problem, index) => (
                  <div key={index} className="border rounded-lg p-6 hover:shadow-lg transition-all duration-200 bg-white">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <span className="font-mono text-lg font-semibold text-gray-900">
                            {formatProblemId(problem)}
                          </span>
                          {problem.rating && (
                            <Badge className={`ml-2 ${getDifficultyColor(problem.rating)}`}>
                              {problem.rating}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openProblemInNewTab(problem)}
                        className="hover:bg-blue-50 hover:border-blue-300"
                      >
                        <ExternalLink className="h-4 w-4 mr-1" />
                        Open in Codeforces
                      </Button>
                    </div>
                    
                    <h3 className="font-semibold text-xl mb-3 text-gray-900">{problem.name}</h3>
                    
                    {problem.tags && problem.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {problem.tags.map((tag, tagIndex) => (
                          <Badge key={tagIndex} variant="outline" className="text-xs bg-gray-50">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start space-x-2">
                        <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div className="text-sm text-blue-800">
                          <p className="font-medium mb-1">Instructions:</p>
                          <ul className="space-y-1 text-blue-700">
                            <li>• Click "Open in Codeforces" to access the problem</li>
                            <li>• Make sure you're logged into your Codeforces account</li>
                            <li>• Submit your solution using the correct programming language</li>
                            <li>• Your progress will be automatically tracked</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <BookOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg">No problems available for this test.</p>
                <p className="text-sm">Please contact the HR team if you believe this is an error.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {registrationStatus === 'success' && (
          <div className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="h-5 w-5 mr-2" />
                  Test Instructions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3 text-gray-900">How to Take the Test:</h4>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-start space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold mt-0.5">1</div>
                        <p>Click "Open in Codeforces" for each problem</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold mt-0.5">2</div>
                        <p>Make sure you're logged into your Codeforces account</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold mt-0.5">3</div>
                        <p>Read the problem statement carefully</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold mt-0.5">4</div>
                        <p>Write and submit your solution</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold mb-3 text-gray-900">Important Notes:</h4>
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-start space-x-2">
                        <Clock className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <p>There's no time limit, but complete as soon as possible</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <p>Your progress is automatically tracked</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <p>Make sure your Codeforces username is correct</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <p>HR team will review your results</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="h-5 w-5 mr-2" />
                  Test Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="mb-4">
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {testQuestions.length} Problems
                    </div>
                    <p className="text-gray-600">Total problems to solve</p>
                  </div>
                  
                  <div className="bg-gray-100 rounded-full h-2 mb-4">
                    <div className="bg-blue-600 h-2 rounded-full" style={{width: '0%'}}></div>
                  </div>
                  
                  <p className="text-sm text-gray-500">
                    Progress will be updated automatically as you solve problems
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default CandidateTest;
