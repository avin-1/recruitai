import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import { CORE_API_BASE } from "@/lib/apiConfig";

const CORE_API = CORE_API_BASE;

const CreateJobProfile = () => {
  const [activeTab, setActiveTab] = useState("chat"); // "chat" or "upload"
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([
    {
      type: "assistant",
      content: "👋 Hello! I'm your Job Description Agent. Describe a job position and I'll create a structured profile for you.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const chatEndRef = useRef(null);

  // File upload state
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  // Profile state (shared between both methods)
  const [generatedProfile, setGeneratedProfile] = useState(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [modifiedData, setModifiedData] = useState({});
  const [actionMessage, setActionMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Handle chat message submission
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isGenerating) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setActionMessage("");

    // Add user message to chat
    const newUserMessage = {
      type: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, newUserMessage]);

    // Show generating message
    setIsGenerating(true);
    const generatingMessage = {
      type: "assistant",
      content: "🤖 Analyzing your job description and creating a structured profile...",
      timestamp: new Date().toISOString(),
      isGenerating: true,
    };
    setChatMessages((prev) => [...prev, generatingMessage]);

    try {
      // Call API to create job profile
      const res = await axios.post(`${CORE_API}/create-job-profile`, {
        job_description: userMessage,
      });

      // Remove generating message and add success message
      setChatMessages((prev) => prev.filter((msg) => !msg.isGenerating));

      const successMessage = {
        type: "assistant",
        content: "✅ Job profile created successfully! Review it below and approve, reject, or modify as needed.",
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, successMessage]);

      // Set generated profile to display
      setGeneratedProfile(res.data.profile);
      setEditingProfile(false);
      setActionMessage("✅ Profile created successfully!");
      
      // Clear message after 3 seconds
      setTimeout(() => setActionMessage(""), 3000);
    } catch (err) {
      console.error(err);
      // Remove generating message and add error message
      setChatMessages((prev) => prev.filter((msg) => !msg.isGenerating));

      const errorMessage = {
        type: "assistant",
        content: `❌ Failed to create job profile: ${err.response?.data?.error || err.message}. Please try again with a more detailed description.`,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, errorMessage]);
      setActionMessage("❌ Failed to create profile");
      setTimeout(() => setActionMessage(""), 3000);
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle file upload
  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      setActionMessage("");
    } else {
      setActionMessage("⚠️ Please select a valid PDF file");
      setTimeout(() => setActionMessage(""), 3000);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setActionMessage("⚠️ Please select a file first!");
      setTimeout(() => setActionMessage(""), 3000);
      return;
    }

    setIsUploading(true);
    setActionMessage("");
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Upload file
      await axios.post(`${CORE_API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      // File uploaded successfully - the backend agent will process it
      // For now, we'll show a message. In production, you might want to poll for the profile
      setActionMessage("✅ PDF uploaded successfully! The profile will be processed and appear in the profiles list shortly.");
      setTimeout(() => setActionMessage(""), 5000);
      
      // Reset file input
      setFile(null);
      setUploadProgress(0);
      
      // Note: In a real implementation, you might want to poll the API or use websockets
      // to get the generated profile automatically. For now, users can check the Profiles page.
    } catch (err) {
      console.error(err);
      setActionMessage(`❌ Upload failed: ${err.response?.data?.error || err.message}`);
      setTimeout(() => setActionMessage(""), 3000);
    } finally {
      setIsUploading(false);
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile);
        setActionMessage("");
      } else {
        setActionMessage("⚠️ Please drop a valid PDF file");
        setTimeout(() => setActionMessage(""), 3000);
      }
    }
  };

  // Handle input changes during edit
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setModifiedData({ ...modifiedData, [name]: value });
  };

  // Handle textarea changes for array fields
  const handleTextAreaChange = (e) => {
    const { name, value } = e.target;
    setModifiedData({
      ...modifiedData,
      [name]: value.split("\n").filter((line) => line.trim()),
    });
  };

  // Enter edit mode
  const handleEdit = () => {
    setEditingProfile(true);
    setModifiedData({ ...generatedProfile });
    setActionMessage("");
  };

  // Cancel edit mode
  const handleCancelEdit = () => {
    setEditingProfile(false);
    setModifiedData({});
  };

  // Approve profile
  const handleApprove = async () => {
    if (!generatedProfile?._id) return;

    setIsProcessing(true);
    setActionMessage("");

    try {
      await axios.post(`${CORE_API}/approve`, {
        profile_id: generatedProfile._id,
      });

      setGeneratedProfile({ ...generatedProfile, approved: true });
      setActionMessage("✅ Profile approved successfully!");

      // Add to chat if in chat mode
      if (activeTab === "chat") {
        setChatMessages((prev) => [
          ...prev,
          {
            type: "assistant",
            content: "✅ Profile has been approved and is now active in the system.",
            timestamp: new Date().toISOString(),
          },
        ]);
      }

      setTimeout(() => setActionMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setActionMessage("❌ Failed to approve profile");
      setTimeout(() => setActionMessage(""), 3000);
    } finally {
      setIsProcessing(false);
    }
  };

  // Reject profile
  const handleReject = async () => {
    if (!generatedProfile?._id) return;

    if (
      !window.confirm(
        "Are you sure you want to reject this profile? It will be deleted."
      )
    ) {
      return;
    }

    setIsProcessing(true);
    setActionMessage("");

    try {
      await axios.post(`${CORE_API}/delete`, {
        profile_id: generatedProfile._id,
      });

      setGeneratedProfile(null);
      setEditingProfile(false);
      setModifiedData({});
      setActionMessage("❌ Profile rejected and deleted");

      // Add to chat if in chat mode
      if (activeTab === "chat") {
        setChatMessages((prev) => [
          ...prev,
          {
            type: "assistant",
            content: "❌ Profile has been rejected and removed from the system.",
            timestamp: new Date().toISOString(),
          },
        ]);
      }

      setTimeout(() => setActionMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setActionMessage("❌ Failed to reject profile");
      setTimeout(() => setActionMessage(""), 3000);
    } finally {
      setIsProcessing(false);
    }
  };

  // Save modified profile
  const handleSave = async () => {
    if (!generatedProfile?._id) return;

    setIsProcessing(true);
    setActionMessage("");

    try {
      await axios.post(`${CORE_API}/modify`, {
        profile_id: generatedProfile._id,
        new_profile_data: modifiedData,
      });

      // When a profile is modified, it's automatically set to approved: false by the backend
      setGeneratedProfile({ ...modifiedData, _id: generatedProfile._id, approved: false });
      setEditingProfile(false);
      setActionMessage("✅ Profile modified and saved! It now requires re-approval.");

      // Add to chat if in chat mode
      if (activeTab === "chat") {
        setChatMessages((prev) => [
          ...prev,
          {
            type: "assistant",
            content: "✅ Profile has been modified. Please review and approve when ready.",
            timestamp: new Date().toISOString(),
          },
        ]);
      }

      setTimeout(() => setActionMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setActionMessage("❌ Failed to save profile");
      setTimeout(() => setActionMessage(""), 3000);
    } finally {
      setIsProcessing(false);
    }
  };

  // Create new profile (clear current)
  const handleCreateNew = () => {
    if (
      generatedProfile &&
      !window.confirm(
        "Create a new profile? Current profile will be cleared from view."
      )
    ) {
      return;
    }
    setGeneratedProfile(null);
    setEditingProfile(false);
    setModifiedData({});
    setActionMessage("");
    setFile(null);
    setUploadProgress(0);
    if (activeTab === "chat") {
      setChatMessages([
        {
          type: "assistant",
          content: "👋 Ready to create a new job profile! Describe the position you'd like to add.",
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  return (
    <main className="flex-1 p-6 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 min-h-screen relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl lg:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Create Job Profile
          </h1>
          <p className="text-gray-700 text-lg font-medium">
            Create structured job profiles using AI-powered chat or upload a PDF
          </p>
        </div>

        {/* Action Message */}
        {actionMessage && (
          <div
            className={`mb-4 p-4 rounded-xl border backdrop-blur-md shadow-lg ${
              actionMessage.startsWith("✅")
                ? "bg-green-500/20 border-green-300/50 text-green-900 backdrop-blur-sm"
                : actionMessage.startsWith("⚠️")
                ? "bg-yellow-500/20 border-yellow-300/50 text-yellow-900 backdrop-blur-sm"
                : "bg-red-500/20 border-red-300/50 text-red-900 backdrop-blur-sm"
            }`}
          >
            {actionMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Side: Input Methods (Tabs) */}
          <Card className="flex flex-col h-[calc(100vh-12rem)] backdrop-blur-xl bg-white/40 border-white/20 shadow-2xl">
            <CardHeader className="border-b border-white/30 bg-gradient-to-r from-blue-500/10 to-indigo-500/10 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent font-bold">Create Profile</CardTitle>
                  <CardDescription className="mt-2 text-gray-700 font-medium">
                    Choose your preferred method to create a job profile
                  </CardDescription>
                </div>
                {generatedProfile && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleCreateNew} 
                    className="bg-white/60 backdrop-blur-sm border-white/30 hover:bg-white/80 shadow-md"
                  >
                    New Profile
                  </Button>
                )}
              </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden min-h-0">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
                <div className="px-6 pt-4 border-b border-white/30 bg-white/20 backdrop-blur-sm flex-shrink-0">
                  <TabsList className="grid w-full grid-cols-2 bg-white/40 backdrop-blur-sm border border-white/30 p-1 rounded-lg">
                    <TabsTrigger 
                      value="chat"
                      className="data-[state=active]:bg-white/80 data-[state=active]:shadow-lg backdrop-blur-sm transition-all"
                    >
                      💬 Chat Assistant
                    </TabsTrigger>
                    <TabsTrigger 
                      value="upload"
                      className="data-[state=active]:bg-white/80 data-[state=active]:shadow-lg backdrop-blur-sm transition-all"
                    >
                      📄 Upload PDF
                    </TabsTrigger>
                  </TabsList>
                </div>

                {/* Chat Tab */}
                <TabsContent value="chat" className="flex-1 flex flex-col m-0 p-0 overflow-hidden min-h-0">
                  {/* Chat Messages */}
                  <div className="chat-messages flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-white/30 via-white/20 to-white/10 backdrop-blur-sm min-h-0" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(59, 130, 246, 0.4) rgba(255, 255, 255, 0.1)' }}>
                    <style>{`
                      .chat-messages::-webkit-scrollbar {
                        width: 8px;
                      }
                      .chat-messages::-webkit-scrollbar-track {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 4px;
                      }
                      .chat-messages::-webkit-scrollbar-thumb {
                        background: rgba(59, 130, 246, 0.4);
                        border-radius: 4px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                      }
                      .chat-messages::-webkit-scrollbar-thumb:hover {
                        background: rgba(59, 130, 246, 0.6);
                      }
                    `}</style>
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${
                          msg.type === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-[80%] rounded-2xl px-4 py-3 backdrop-blur-md transition-all hover:scale-[1.02] ${
                            msg.type === "user"
                              ? "bg-gradient-to-r from-blue-600/90 to-indigo-600/90 text-white shadow-xl border border-white/30"
                              : "bg-white/70 backdrop-blur-md border border-white/50 text-gray-800 shadow-xl"
                          }`}
                        >
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">
                            {msg.content}
                          </p>
                          <p
                            className={`text-xs mt-2 ${
                              msg.type === "user"
                                ? "text-blue-100/90"
                                : "text-gray-600"
                            }`}
                          >
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat Input */}
                  <div className="border-t border-white/30 bg-white/50 backdrop-blur-md p-4 shadow-lg flex-shrink-0">
                    <form onSubmit={handleChatSubmit} className="flex gap-3">
                      <Textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        placeholder="Example: I need a Senior Software Engineer at TechCorp in San Francisco. Requirements: 5+ years Python, React, AWS experience. Bachelor's degree in CS required..."
                        className="flex-1 min-h-[80px] resize-none bg-white/70 backdrop-blur-sm border-white/40 focus:bg-white/90 focus:border-blue-400/50 shadow-md"
                        disabled={isGenerating}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleChatSubmit(e);
                          }
                        }}
                      />
                      <Button
                        type="submit"
                        disabled={isGenerating || !inputMessage.trim()}
                        className="self-end h-[80px] px-6 bg-gradient-to-r from-blue-600/90 to-indigo-600/90 hover:from-blue-700 hover:to-indigo-700 backdrop-blur-sm border border-white/20 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isGenerating ? (
                          <span className="flex items-center gap-2">
                            <span className="animate-spin">⏳</span>
                            Generating...
                          </span>
                        ) : (
                          "Send"
                        )}
                      </Button>
                    </form>
                    <p className="text-xs text-gray-600 mt-2 font-medium">
                      Press Enter to send, Shift+Enter for new line
                    </p>
                  </div>
                </TabsContent>

                {/* Upload Tab */}
                <TabsContent value="upload" className="flex-1 flex flex-col m-0 p-0 overflow-hidden">
                  <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    <div className="flex items-center justify-center min-h-[300px]">
                      <div
                        className={`w-full border-2 border-dashed rounded-lg p-12 text-center transition-all ${
                          isDragging
                            ? "border-blue-500 bg-blue-50 scale-105"
                            : "border-white/40 bg-white/30 hover:border-blue-400/50 hover:bg-white/40 backdrop-blur-sm"
                        }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                      >
                        <input
                          type="file"
                          accept=".pdf"
                          onChange={handleFileChange}
                          className="hidden"
                          id="file-upload"
                        />
                        <label htmlFor="file-upload" className="cursor-pointer">
                          <div className="text-6xl mb-4">📄</div>
                          <p className="text-lg font-medium text-gray-700 mb-2">
                            {file
                              ? file.name
                              : "Drag and drop a PDF file here"}
                          </p>
                          <p className="text-sm text-gray-500 mb-4">
                            or click to browse
                          </p>
                          {!file && (
                            <p className="text-xs text-gray-400">
                              Only PDF files are supported
                            </p>
                          )}
                        </label>
                      </div>
                    </div>

                    {uploadProgress > 0 && (
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                          className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                    )}

                    <Button
                      onClick={handleUpload}
                      disabled={!file || isUploading}
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 h-12 text-lg"
                    >
                      {isUploading ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="animate-spin">⏳</span>
                          Uploading... {uploadProgress}%
                        </span>
                      ) : (
                        "📤 Upload PDF"
                      )}
                    </Button>

                    <div className="bg-blue-500/20 backdrop-blur-md border border-blue-300/50 rounded-xl p-4 mb-4 shadow-lg">
                      <p className="text-sm text-blue-900 font-medium">
                        <strong>ℹ️ Note:</strong> After uploading, the PDF will be
                        processed by the AI agent. Check the{" "}
                        <strong>View Profiles</strong> page to see the generated
                        profile.
                      </p>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Right Side: Profile Preview & Actions */}
          <Card className="flex flex-col h-[calc(100vh-12rem)] bg-white/70 backdrop-blur-xl border border-white/30 shadow-2xl">
            <CardHeader className="border-b border-white/30 bg-gradient-to-r from-purple-50/80 to-pink-50/80 backdrop-blur-md">
              <CardTitle className="text-2xl bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent font-bold">📄 Generated Profile</CardTitle>
              <CardDescription className="mt-2 text-gray-700 font-medium">
                Review and manage the created job profile
              </CardDescription>
            </CardHeader>

            <CardContent className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-white/20 to-white/10 backdrop-blur-sm scrollbar-thin scrollbar-thumb-purple-300/50 scrollbar-track-transparent">
              {generatedProfile ? (
                <div className="space-y-6">
                  {editingProfile ? (
                    // Edit Mode
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Job Title *
                        </label>
                        <input
                          type="text"
                          name="job_title"
                          value={modifiedData.job_title || ""}
                          onChange={handleInputChange}
                          className="w-full px-4 py-2 bg-white/70 backdrop-blur-sm border border-white/40 rounded-lg focus:ring-2 focus:ring-blue-500/50 focus:bg-white/90 focus:border-blue-400/50 shadow-md"
                          placeholder="e.g., Senior Software Engineer"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Company *
                          </label>
                          <input
                            type="text"
                            name="company"
                            value={modifiedData.company || ""}
                            onChange={handleInputChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Location
                          </label>
                          <input
                            type="text"
                            name="location"
                            value={modifiedData.location || ""}
                            onChange={handleInputChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., San Francisco, CA"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Experience Level
                          </label>
                          <input
                            type="text"
                            name="experience_level"
                            value={modifiedData.experience_level || ""}
                            onChange={handleInputChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., 5+ years"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Education
                          </label>
                          <input
                            type="text"
                            name="educational_requirements"
                            value={modifiedData.educational_requirements || ""}
                            onChange={handleInputChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., Bachelor's in CS"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Responsibilities (one per line)
                        </label>
                        <Textarea
                          name="responsibilities"
                          value={
                            Array.isArray(modifiedData.responsibilities)
                              ? modifiedData.responsibilities.join("\n")
                              : modifiedData.responsibilities || ""
                          }
                          onChange={handleTextAreaChange}
                          className="w-full min-h-[120px]"
                          placeholder="Enter responsibilities, one per line"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Required Skills (one per line)
                        </label>
                        <Textarea
                          name="required_skills"
                          value={
                            Array.isArray(modifiedData.required_skills)
                              ? modifiedData.required_skills.join("\n")
                              : modifiedData.required_skills || ""
                          }
                          onChange={handleTextAreaChange}
                          className="w-full min-h-[120px]"
                          placeholder="Enter skills, one per line"
                        />
                      </div>

                      <div className="flex gap-3 pt-4 border-t">
                        <Button
                          onClick={handleSave}
                          disabled={isProcessing}
                          className="flex-1 bg-gradient-to-r from-green-600/90 to-green-700/90 hover:from-green-700 hover:to-green-800 backdrop-blur-sm border border-white/20 shadow-lg"
                        >
                          {isProcessing ? "Saving..." : "💾 Save Changes"}
                        </Button>
                        <Button
                          onClick={handleCancelEdit}
                          variant="outline"
                          disabled={isProcessing}
                          className="bg-white/60 backdrop-blur-sm border-white/30 hover:bg-white/80"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-4">
                      <div className="flex items-start justify-between pb-4 border-b">
                        <div>
                          <h3 className="text-2xl font-bold text-gray-900">
                            {generatedProfile.job_title || "Untitled Position"}
                          </h3>
                          <div className="flex items-center gap-2 mt-2">
                            {generatedProfile.approved ? (
                              <Badge className="bg-green-500/30 backdrop-blur-sm text-green-900 border-green-400/50 shadow-md">
                                ✓ Approved
                              </Badge>
                            ) : (
                              <Badge className="bg-yellow-500/30 backdrop-blur-sm text-yellow-900 border-yellow-400/50 shadow-md">
                                ⏳ Pending Approval
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-white/50 backdrop-blur-sm border border-white/30 p-3 rounded-lg shadow-md">
                          <p className="text-xs text-gray-500 mb-1">Company</p>
                          <p className="font-medium text-gray-900">
                            {generatedProfile.company || "N/A"}
                          </p>
                        </div>
                        <div className="bg-white/50 backdrop-blur-sm border border-white/30 p-3 rounded-lg shadow-md">
                          <p className="text-xs text-gray-500 mb-1">Location</p>
                          <p className="font-medium text-gray-900">
                            {generatedProfile.location || "N/A"}
                          </p>
                        </div>
                        <div className="bg-white/50 backdrop-blur-sm border border-white/30 p-3 rounded-lg shadow-md">
                          <p className="text-xs text-gray-500 mb-1">
                            Experience
                          </p>
                          <p className="font-medium text-gray-900">
                            {generatedProfile.experience_level || "N/A"}
                          </p>
                        </div>
                        <div className="bg-white/50 backdrop-blur-sm border border-white/30 p-3 rounded-lg shadow-md">
                          <p className="text-xs text-gray-500 mb-1">Education</p>
                          <p className="font-medium text-gray-900">
                            {generatedProfile.educational_requirements || "N/A"}
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">
                          Responsibilities
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 bg-white/50 backdrop-blur-sm border border-white/30 p-4 rounded-lg shadow-md">
                          {Array.isArray(generatedProfile.responsibilities) &&
                          generatedProfile.responsibilities.length > 0 ? (
                            generatedProfile.responsibilities.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))
                          ) : (
                            <li className="text-gray-500 italic">
                              No responsibilities listed
                            </li>
                          )}
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">
                          Required Skills
                        </h4>
                        <div className="flex flex-wrap gap-2 bg-white/50 backdrop-blur-sm border border-white/30 p-4 rounded-lg shadow-md">
                          {Array.isArray(generatedProfile.required_skills) &&
                          generatedProfile.required_skills.length > 0 ? (
                            generatedProfile.required_skills.map((skill, idx) => (
                              <Badge key={idx} variant="outline" className="bg-white/80 backdrop-blur-sm border-white/40">
                                {skill}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-gray-500 italic">
                              No skills listed
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-3 pt-4 border-t">
                        {!generatedProfile.approved && (
                          <Button
                            onClick={handleApprove}
                            disabled={isProcessing}
                            className="flex-1 bg-gradient-to-r from-green-600/90 to-green-700/90 hover:from-green-700 hover:to-green-800 backdrop-blur-sm border border-white/20 shadow-lg"
                          >
                            ✓ Approve Profile
                          </Button>
                        )}
                        <Button
                          onClick={handleEdit}
                          variant="outline"
                          disabled={isProcessing}
                          className="flex-1 bg-white/60 backdrop-blur-sm border-white/30 hover:bg-white/80"
                        >
                          ✏️ Edit
                        </Button>
                        <Button
                          onClick={handleReject}
                          variant="outline"
                          disabled={isProcessing}
                          className="bg-red-500/20 backdrop-blur-sm text-red-700 border-red-400/50 hover:bg-red-500/30"
                        >
                          🗑️ Reject
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <div className="text-6xl mb-4">📝</div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No Profile Generated Yet
                  </h3>
                  <p className="text-gray-600 max-w-md">
                    {activeTab === "chat"
                      ? "Start a conversation in the chat interface to create a job profile. The AI will analyze your description and generate a structured profile for review."
                      : "Upload a PDF or use the chat interface to create a job profile. The generated profile will appear here for review."}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
};

export default CreateJobProfile;
