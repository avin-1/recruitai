import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter
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
  AlertDescription,
  AlertTitle
} from '@/components/ui/alert';
import {
  Badge
} from '@/components/ui/badge';
import {
  RadioGroup,
  RadioGroupItem
} from '@/components/ui/radio-group';
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
  Info,
  ChevronRight,
  Menu,
  Code,
  FileText,
  CheckSquare,
  Send
} from 'lucide-react';
import { SHORTLISTING_API_BASE } from '@/lib/apiConfig';

const API_BASE_URL = SHORTLISTING_API_BASE;

const CandidateTest = () => {
  const { testId } = useParams();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testData, setTestData] = useState(null); // Normalized data: { sections: [] }
  const [testInfo, setTestInfo] = useState(null);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [answers, setAnswers] = useState({}); // { [sectionId_questionIndex]: answer }

  // Registration State
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
      // Check for saved registration
      const savedRegistration = localStorage.getItem(`test_registration_${testId}`);
      if (savedRegistration) {
        try {
          const parsed = JSON.parse(savedRegistration);
          setRegistrationForm(parsed);
          setRegistrationStatus('success');
        } catch (e) {
          console.error('Error parsing saved registration', e);
        }
      }
    }
  }, [testId]);

  const loadTestInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/tests/${testId}/questions`);
      const data = await response.json();

      if (data.success) {
        setTestInfo(data.test_info);

        // Normalize questions data
        let sections = [];
        if (Array.isArray(data.questions)) {
          // Check if it's a flat list of Codeforces problems (Legacy)
          // or a list of Section objects (New)
          const isLegacy = data.questions.length > 0 && !data.questions[0].questions;

          if (isLegacy) {
            sections = [{
              id: 'default',
              name: 'Problem Set',
              questions: data.questions
            }];
          } else {
            sections = data.questions;
          }
        }

        setTestData({ sections });
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
        // Save to localStorage
        localStorage.setItem(`test_registration_${testId}`, JSON.stringify(registrationForm));
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

  const handleAnswerChange = (sectionId, questionIndex, value) => {
    setAnswers(prev => ({
      ...prev,
      [`${sectionId}_${questionIndex}`]: value
    }));
  };

  const formatProblemId = (problem) => {
    if (problem.contestId && problem.index) {
      return `${problem.contestId}${problem.index}`;
    }
    return '';
  };

  const getDifficultyColor = (rating) => {
    if (!rating) return 'bg-gray-100 text-gray-800';
    if (rating <= 1000) return 'bg-green-100 text-green-800';
    if (rating <= 1200) return 'bg-green-100 text-green-800';
    if (rating <= 1400) return 'bg-blue-100 text-blue-800';
    if (rating <= 1600) return 'bg-purple-100 text-purple-800';
    if (rating <= 1800) return 'bg-yellow-100 text-yellow-800';
    if (rating <= 2000) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const openProblemInNewTab = (problem) => {
    // Handle both legacy Codeforces object and new question object structure
    const data = problem.data || problem;
    const url = `https://codeforces.com/problemset/problem/${data.contestId}/${data.index}`;
    window.open(url, '_blank');
  };

  // Renderers for different question types
  const renderQuestion = (question, index, sectionId) => {
    const answerKey = `${sectionId}_${index}`;

    // 1. Codeforces Question
    if (question.type === 'codeforces' || (!question.type && question.contestId)) {
      const problemData = question.data || question;
      return (
        <Card key={index} className="mb-6 border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="font-mono">
                  {formatProblemId(problemData)}
                </Badge>
                <CardTitle className="text-lg">{problemData.name}</CardTitle>
              </div>
              {problemData.rating && (
                <Badge className={getDifficultyColor(problemData.rating)}>
                  {problemData.rating}
                </Badge>
              )}
            </div>
            <CardDescription className="flex gap-2 mt-1">
              {problemData.tags?.map(tag => (
                <span key={tag} className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                  {tag}
                </span>
              ))}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-purple-50 p-4 rounded-lg flex items-start gap-3">
              <Code className="h-5 w-5 text-purple-600 mt-1 flex-shrink-0" />
              <div className="text-sm text-purple-900">
                <p className="font-medium mb-1">Coding Challenge</p>
                <p>Solve this problem on Codeforces. Your submission will be automatically tracked.</p>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              variant="outline"
              className="w-full sm:w-auto gap-2"
              onClick={() => openProblemInNewTab(question)}
            >
              <ExternalLink className="h-4 w-4" />
              Open Problem on Codeforces
            </Button>
          </CardFooter>
        </Card>
      );
    }

    // 2. Multiple Choice Question
    if (question.options && question.options.length > 0) {
      return (
        <Card key={index} className="mb-6 border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="text-lg font-medium flex gap-3">
              <span className="bg-blue-100 text-blue-700 w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0">
                {index + 1}
              </span>
              {question.question}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <RadioGroup
              value={answers[answerKey] || ''}
              onValueChange={(val) => handleAnswerChange(sectionId, index, val)}
              className="space-y-3"
            >
              {question.options.map((opt, optIdx) => (
                <div key={optIdx} className="flex items-center space-x-2 border p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <RadioGroupItem value={opt} id={`${answerKey}_${optIdx}`} />
                  <Label htmlFor={`${answerKey}_${optIdx}`} className="flex-1 cursor-pointer font-normal">
                    {opt}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </CardContent>
        </Card>
      );
    }

    // 3. Text/Open Question
    return (
      <Card key={index} className="mb-6 border-l-4 border-l-green-500">
        <CardHeader>
          <CardTitle className="text-lg font-medium flex gap-3">
            <span className="bg-green-100 text-green-700 w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0">
              {index + 1}
            </span>
            {question.question}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor={answerKey}>Your Answer</Label>
            <textarea
              id={answerKey}
              className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Type your answer here..."
              value={answers[answerKey] || ''}
              onChange={(e) => handleAnswerChange(sectionId, index, e.target.value)}
            />
          </div>
        </CardContent>
      </Card>
    );
  };

  // Loading State
  if (loading && !testInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600 font-medium">Loading test environment...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (registrationStatus === 'error' && !testInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="bg-red-50 border-b border-red-100">
            <CardTitle className="text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> Error
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <p className="text-gray-700 mb-6">{errorMessage}</p>
            <Button onClick={() => navigate('/')} variant="outline" className="w-full">
              Return to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Registration View
  if (registrationStatus === 'pending') {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 flex flex-col items-center">
        <div className="w-full max-w-3xl space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
              Technical Assessment
            </h1>
            {testInfo && (
              <div className="mt-4">
                <h2 className="text-2xl font-semibold text-blue-600">{testInfo.name}</h2>
                <p className="mt-2 text-gray-600 max-w-2xl mx-auto">{testInfo.description}</p>
              </div>
            )}
          </div>

          <Card className="shadow-xl border-0 overflow-hidden">
            <div className="bg-blue-600 p-6 text-white">
              <h3 className="text-xl font-bold flex items-center gap-2">
                <User className="h-6 w-6" /> Candidate Registration
              </h3>
              <p className="text-blue-100 mt-1">Please enter your details to begin the assessment.</p>
            </div>
            <CardContent className="p-8">
              <form onSubmit={handleRegistration} className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-base">Email Address</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        className="pl-10 h-12"
                        placeholder="you@example.com"
                        value={registrationForm.candidate_email}
                        onChange={(e) => setRegistrationForm({ ...registrationForm, candidate_email: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="cf_user" className="text-base">Codeforces Username</Label>
                    <div className="relative">
                      <Code className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="cf_user"
                        className="pl-10 h-12"
                        placeholder="username"
                        value={registrationForm.codeforces_username}
                        onChange={(e) => setRegistrationForm({ ...registrationForm, codeforces_username: e.target.value })}
                        required
                      />
                    </div>
                    <p className="text-xs text-gray-500">Required for tracking coding problems</p>
                  </div>
                </div>

                {errorMessage && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Registration Failed</AlertTitle>
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                )}

                <Button type="submit" className="w-full h-12 text-lg font-medium bg-blue-600 hover:bg-blue-700" disabled={loading}>
                  {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : 'Start Assessment'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center text-sm text-gray-500">
            <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
              <Clock className="h-6 w-6 mb-2 text-blue-500" />
              <p>Self-paced assessment</p>
            </div>
            <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
              <Target className="h-6 w-6 mb-2 text-green-500" />
              <p>Auto-tracked progress</p>
            </div>
            <div className="flex flex-col items-center p-4 bg-white rounded-lg shadow-sm">
              <CheckSquare className="h-6 w-6 mb-2 text-purple-500" />
              <p>Multiple question types</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Test Interface
  const currentSection = testData?.sections[currentSectionIndex];

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white p-2 rounded-lg">
              <Code className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900 leading-tight">{testInfo?.name}</h1>
              <p className="text-xs text-gray-500">Candidate: {registrationForm.candidate_email}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" className="hidden sm:flex">
            <Info className="h-4 w-4 mr-2" /> Help
          </Button>
        </div>
      </header>

      <div className="flex-1 container mx-auto px-4 py-8 flex flex-col lg:flex-row gap-8">
        {/* Sidebar Navigation */}
        <aside className="w-full lg:w-64 flex-shrink-0 space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Test Sections
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <nav className="space-y-1">
                {testData?.sections.map((section, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentSectionIndex(idx)}
                    className={`w-full flex items-center justify-between px-4 py-3 text-sm font-medium rounded-md transition-colors ${currentSectionIndex === idx
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                  >
                    <span className="truncate">{section.name || `Section ${idx + 1}`}</span>
                    <Badge variant="secondary" className="ml-2 text-xs">
                      {section.questions?.length || 0}
                    </Badge>
                  </button>
                ))}
              </nav>
            </CardContent>
          </Card>

          <Card className="bg-blue-50 border-blue-100">
            <CardContent className="p-4">
              <h4 className="font-semibold text-blue-900 mb-2 text-sm">Progress</h4>
              <div className="w-full bg-blue-200 rounded-full h-2.5 mb-2">
                <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: '0%' }}></div>
              </div>
              <p className="text-xs text-blue-700">
                Your progress is automatically saved.
              </p>
            </CardContent>
          </Card>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          {currentSection ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">{currentSection.name}</h2>
                <span className="text-sm text-gray-500">
                  {currentSection.questions?.length} Questions
                </span>
              </div>

              {currentSection.questions?.length > 0 ? (
                <div className="space-y-8">
                  {currentSection.questions.map((q, idx) => renderQuestion(q, idx, currentSection.id || idx))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white rounded-lg border border-dashed">
                  <p className="text-gray-500">No questions in this section.</p>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between pt-6 border-t">
                <Button
                  variant="outline"
                  onClick={() => setCurrentSectionIndex(Math.max(0, currentSectionIndex - 1))}
                  disabled={currentSectionIndex === 0}
                >
                  Previous Section
                </Button>

                {currentSectionIndex < (testData.sections.length - 1) ? (
                  <Button
                    onClick={() => setCurrentSectionIndex(currentSectionIndex + 1)}
                  >
                    Next Section <ChevronRight className="h-4 w-4 ml-2" />
                  </Button>
                ) : (
                  <Button
                    className="bg-green-600 hover:bg-green-700"
                    disabled={submitting}
                    onClick={async () => {
                      if (!window.confirm('Are you sure you want to submit your test?')) return;

                      console.log('Submitting with form:', registrationForm);
                      if (!registrationForm.candidate_email) {
                        alert('Error: Candidate email is missing. Please refresh the page and register again.');
                        return;
                      }

                      setSubmitting(true);
                      try {
                        // 1. Submit Manual Answers
                        console.log('Sending answers:', answers);
                        const submitResponse = await fetch(`${API_BASE_URL}/tests/${testId}/submit`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            candidate_email: registrationForm.candidate_email,
                            answers: answers
                          })
                        });

                        // Check for non-OK response
                        if (!submitResponse.ok) {
                          const text = await submitResponse.text();
                          throw new Error(`Server error: ${submitResponse.status} - ${text}`);
                        }

                        // 2. Trigger Codeforces Fetch
                        await fetch(`${API_BASE_URL}/tests/${testId}/fetch-results`, {
                          method: 'POST'
                        });

                        const data = await submitResponse.json();
                        if (data.success) {
                          alert('Test Submitted Successfully!');
                          // Clear registration
                          localStorage.removeItem(`test_registration_${testId}`);
                          navigate('/');
                        } else {
                          alert('Error submitting test: ' + data.error);
                        }
                      } catch (error) {
                        console.error('Submit error:', error);
                        alert(`Failed to submit test: ${error.message}`);
                      } finally {
                        setSubmitting(false);
                      }
                    }}
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    Submit Test <CheckCircle className="h-4 w-4 ml-2" />
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-400" />
            </div>
          )}
        </main>
      </div >
    </div >
  );
};

export default CandidateTest;
