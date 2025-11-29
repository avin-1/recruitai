import React, { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { CORE_API_BASE } from "@/lib/apiConfig";

const API_BASE = CORE_API_BASE;

const Profiles = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [editingProfile, setEditingProfile] = useState(null);
  const [modifiedData, setModifiedData] = useState({});

  // Fetch profiles from backend
  const fetchProfiles = async () => {
    try {
      const res = await axios.get(`${API_BASE}/profiles`);
      setProfiles(res.data.profiles);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setMessage("❌ Failed to load profiles");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

  // Approve profile
  const handleApprove = async (profile_id) => {
    try {
      await axios.post(`${API_BASE}/approve`, { profile_id });
      setProfiles(
        profiles.map((p) =>
          p._id === profile_id ? { ...p, approved: true } : p
        )
      );
      setMessage(`✅ Profile approved`);
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to approve profile`);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  // Disapprove profile (delete)
  const handleDisapprove = async (profile_id) => {
    if (!window.confirm("Are you sure you want to delete this profile?")) {
      return;
    }
    try {
      await axios.post(`${API_BASE}/delete`, { profile_id });
      setProfiles(profiles.filter((p) => p._id !== profile_id));
      setMessage(`❌ Profile deleted`);
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to delete profile`);
      setTimeout(() => setMessage(""), 3000);
    }
  };

  // Enter edit mode
  const handleModify = (profile) => {
    setEditingProfile(profile._id);
    setModifiedData({ ...profile });
  };

  // Cancel edit mode
  const handleCancel = () => {
    setEditingProfile(null);
    setModifiedData({});
  };

  // Save modified profile
  const handleSave = async (profile_id) => {
    try {
      await axios.post(`${API_BASE}/modify`, {
        profile_id,
        new_profile_data: modifiedData,
      });
      // When a profile is modified, it's automatically set to approved: false by the backend
      fetchProfiles();
      setMessage(`✅ Profile modified and saved! It now requires re-approval.`);
      setEditingProfile(null);
      setTimeout(() => setMessage(""), 3000);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to save profile`);
      setTimeout(() => setMessage(""), 3000);
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
    setModifiedData({ ...modifiedData, [name]: value.split("\n").filter(line => line.trim()) });
  };

  if (loading) {
    return (
      <main className="flex-1 p-12 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading profiles...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-6 lg:p-12 page-transition">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl lg:text-5xl font-bold mb-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Job Profiles Management
          </h1>
          <p className="text-gray-700 text-lg font-medium">
            View, approve, reject, or modify job profiles
          </p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-xl border backdrop-blur-md shadow-lg ${
            message.startsWith("✅")
              ? "bg-green-50/90 border-green-200/60 text-green-900"
              : "bg-red-50/90 border-red-200/60 text-red-900"
          }`}>
            {message}
          </div>
        )}

        {/* Profiles List */}
        {profiles.length === 0 ? (
          <Card className="p-12 bg-white/70 backdrop-blur-xl border border-white/30 shadow-xl">
            <div className="text-center">
              <div className="text-6xl mb-4 animate-float">📭</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Profiles Found
              </h3>
              <p className="text-gray-600">
                Create a new job profile using the "Create Job Profile" page.
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {profiles.map((profile) => (
              <Card key={profile._id} className="overflow-hidden bg-white/70 backdrop-blur-xl border border-white/30 shadow-lg hover:shadow-2xl transition-all duration-300">
                <CardHeader className="bg-gradient-to-r from-blue-50/80 to-indigo-50/80 backdrop-blur-md border-b border-white/30">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-2xl mb-2">
                        {profile.job_title || "Untitled Position"}
                      </CardTitle>
                      <div className="flex items-center gap-2">
                        {profile.approved ? (
                          <Badge className="bg-green-100 text-green-800 border-green-300">
                            ✓ Approved
                          </Badge>
                        ) : (
                          <Badge className="bg-yellow-100 text-yellow-800 border-yellow-300">
                            ⏳ Pending Approval
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="p-6">
                  {editingProfile === profile._id ? (
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
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                        />
                      </div>

                      <div className="flex gap-3 pt-4 border-t">
                        <Button
                          onClick={() => handleSave(profile._id)}
                          className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
                        >
                          💾 Save Changes
                        </Button>
                        <Button onClick={handleCancel} variant="outline">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Company</p>
                          <p className="font-medium text-gray-900">
                            {profile.company || "N/A"}
                          </p>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Location</p>
                          <p className="font-medium text-gray-900">
                            {profile.location || "N/A"}
                          </p>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Experience</p>
                          <p className="font-medium text-gray-900">
                            {profile.experience_level || "N/A"}
                          </p>
                        </div>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-xs text-gray-500 mb-1">Education</p>
                          <p className="font-medium text-gray-900">
                            {profile.educational_requirements || "N/A"}
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">
                          Responsibilities
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 bg-gray-50 p-4 rounded-lg">
                          {Array.isArray(profile.responsibilities) &&
                          profile.responsibilities.length > 0 ? (
                            profile.responsibilities.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))
                          ) : (
                            <li className="text-gray-500 italic">No responsibilities listed</li>
                          )}
                        </ul>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">
                          Required Skills
                        </h4>
                        <div className="flex flex-wrap gap-2 bg-gray-50 p-4 rounded-lg">
                          {Array.isArray(profile.required_skills) &&
                          profile.required_skills.length > 0 ? (
                            profile.required_skills.map((skill, idx) => (
                              <Badge key={idx} variant="outline" className="bg-white">
                                {skill}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-gray-500 italic">No skills listed</span>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-3 pt-4 border-t">
                        {!profile.approved && (
                          <Button
                            onClick={() => handleApprove(profile._id)}
                            className="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
                          >
                            ✓ Approve
                          </Button>
                        )}
                        <Button
                          onClick={() => handleModify(profile)}
                          variant="outline"
                          className="flex-1"
                        >
                          ✏️ Modify
                        </Button>
                        <Button
                          onClick={() => handleDisapprove(profile._id)}
                          variant="outline"
                          className="bg-red-50 text-red-700 border-red-300 hover:bg-red-100"
                        >
                          🗑️ Delete
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
};

export default Profiles;
