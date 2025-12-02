import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from '@/components/ui/card';
import {
  Button
} from '@/components/ui/button';
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
  Alert,
  AlertDescription
} from '@/components/ui/alert';
import {
  Loader2,
  Settings as SettingsIcon,
  Sparkles,
  RotateCcw,
  Save,
  Brain
} from 'lucide-react';
import { SHORTLISTING_API_BASE } from '@/lib/apiConfig';

const API_BASE_URL = SHORTLISTING_API_BASE;

const Settings = () => {
  const [loading, setLoading] = useState(false);
  const [prompts, setPrompts] = useState({});
  const [selectedAgent, setSelectedAgent] = useState("Test Generation Agent");
  const [instruction, setInstruction] = useState("");
  const [modifying, setModifying] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/settings/prompts`);
      const data = await response.json();
      if (data.success) {
        setPrompts(data.prompts);
      } else {
        setMessage({ type: 'error', text: 'Failed to load prompts' });
      }
    } catch (error) {
      console.error('Error fetching prompts:', error);
      setMessage({ type: 'error', text: 'Network error loading prompts' });
    } finally {
      setLoading(false);
    }
  };

  const handleModify = async () => {
    if (!instruction.trim()) {
      setMessage({ type: 'error', text: 'Please enter an instruction' });
      return;
    }

    setModifying(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/settings/prompts/modify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: selectedAgent,
          instruction: instruction
        })
      });
      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Prompt updated successfully!' });
        setInstruction("");
        await fetchPrompts();
      } else {
        setMessage({ type: 'error', text: 'Failed to update prompt: ' + data.error });
      }
    } catch (error) {
      console.error('Error modifying prompt:', error);
      setMessage({ type: 'error', text: 'Network error modifying prompt' });
    } finally {
      setModifying(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset this prompt to its default value?')) return;

    setModifying(true);
    try {
      const response = await fetch(`${API_BASE_URL}/settings/prompts/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: selectedAgent
        })
      });
      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: 'Prompt reset to default' });
        await fetchPrompts();
      } else {
        setMessage({ type: 'error', text: 'Failed to reset prompt: ' + data.error });
      }
    } catch (error) {
      console.error('Error resetting prompt:', error);
      setMessage({ type: 'error', text: 'Network error resetting prompt' });
    } finally {
      setModifying(false);
    }
  };

  const currentPromptData = prompts[selectedAgent] || {};

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3 text-gray-900">
          <SettingsIcon className="h-8 w-8 text-gray-700" />
          Agent Settings
        </h1>
        <p className="text-gray-600 mt-2">
          Configure and customize the behavior of your AI agents.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel: Agent Selection */}
        <Card className="lg:col-span-1 h-fit">
          <CardHeader>
            <CardTitle>Select Agent</CardTitle>
            <CardDescription>Choose an agent to configure</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.keys(prompts).map(agent => (
                <button
                  key={agent}
                  onClick={() => setSelectedAgent(agent)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center justify-between ${selectedAgent === agent
                      ? 'bg-blue-50 text-blue-700 border border-blue-200 font-medium'
                      : 'hover:bg-gray-50 text-gray-700 border border-transparent'
                    }`}
                >
                  {agent}
                  {prompts[agent]?.is_custom && (
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                      Custom
                    </span>
                  )}
                </button>
              ))}
              {loading && Object.keys(prompts).length === 0 && (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Right Panel: Prompt Configuration */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>System Prompt Configuration</span>
              {currentPromptData.is_custom && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReset}
                  disabled={modifying}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Restore Default
                </Button>
              )}
            </CardTitle>
            <CardDescription>
              View and modify the instructions that guide the {selectedAgent}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {message && (
              <Alert className={message.type === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
                <AlertDescription className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
                  {message.text}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Current System Prompt</label>
              <div className="relative">
                <Textarea
                  value={currentPromptData.current || ''}
                  readOnly
                  className="min-h-[300px] font-mono text-sm bg-gray-50 text-gray-600 resize-none"
                />
                <div className="absolute top-2 right-2">
                  <span className="text-xs text-gray-400 bg-white px-2 py-1 rounded border">
                    Read-only
                  </span>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                This prompt contains placeholders (e.g., {'{topic}'}) that are filled dynamically.
              </p>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 space-y-4">
              <div className="flex items-center gap-2 text-blue-800 font-medium">
                <Sparkles className="h-5 w-5" />
                Modify with AI
              </div>
              <p className="text-sm text-blue-600">
                Describe how you want to change the agent's behavior. The AI will rewrite the prompt for you while keeping necessary technical requirements.
              </p>
              <div className="flex gap-2">
                <Textarea
                  placeholder="e.g., 'Make the tone more formal and professional' or 'Ask harder questions'"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  className="bg-white min-h-[80px]"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={handleModify}
                  disabled={modifying || !instruction.trim()}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {modifying ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Optimizing Prompt...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4 mr-2" />
                      Update Prompt
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
