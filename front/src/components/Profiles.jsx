import React, { useEffect, useState } from "react";
import axios from "axios";

const Profiles = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [editingProfile, setEditingProfile] = useState(null); // Tracks the _id of the profile being edited
  const [modifiedData, setModifiedData] = useState({});

  // Fetch profiles from backend
  const fetchProfiles = async () => {
    try {
      const res = await axios.get("http://localhost:8080/profiles");
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
      await axios.post(`http://localhost:8080/approve`, { profile_id });
      setProfiles(
        profiles.map((p) =>
          p._id === profile_id ? { ...p, approved: true } : p
        )
      );
      setMessage(`✅ Profile approved`);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to approve profile`);
    }
  };

  // Disapprove profile (delete)
  const handleDisapprove = async (profile_id) => {
    try {
      await axios.post(`http://localhost:8080/delete`, { profile_id });
      setProfiles(profiles.filter((p) => p._id !== profile_id));
      setMessage(`❌ Profile deleted`);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to delete profile`);
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
      await axios.post(`http://localhost:8080/modify`, {
        profile_id,
        new_profile_data: modifiedData,
      });
      // a new profile is created, so we fetch all profiles again
      fetchProfiles();
      setMessage(`✅ Profile modified and saved`);
      setEditingProfile(null);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to save profile`);
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
    setModifiedData({ ...modifiedData, [name]: value.split('\n') });
  };

  if (loading) {
    return <p className="text-center mt-10 text-gray-600">Loading...</p>;
  }

  return (
    <main className="flex-1 p-12">
      <div className="bg-white shadow-lg rounded-lg p-10 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold mb-8 text-gray-800">
          📄 View Job Profiles
        </h2>

        {message && (
          <p className="mb-4 text-center font-medium text-red-600">{message}</p>
        )}

        <div className="overflow-x-auto">
          {profiles.map((profile) => (
            <div
              key={profile._id}
              className="mb-8 p-6 border rounded-lg shadow-sm"
            >
              {editingProfile === profile._id ? (
                // Edit mode
                <div>
                  <input
                    type="text"
                    name="job_title"
                    value={modifiedData.job_title}
                    onChange={handleInputChange}
                    className="text-2xl font-semibold mb-2 w-full"
                  />
                  <input
                    type="text"
                    name="company"
                    value={modifiedData.company}
                    onChange={handleInputChange}
                    className="w-full mb-1"
                  />
                  <input
                    type="text"
                    name="location"
                    value={modifiedData.location}
                    onChange={handleInputChange}
                    className="w-full mb-1"
                  />
                  <input
                    type="text"
                    name="experience_level"
                    value={modifiedData.experience_level}
                    onChange={handleInputChange}
                    className="w-full mb-1"
                  />
                  <input
                    type="text"
                    name="educational_requirements"
                    value={modifiedData.educational_requirements}
                    onChange={handleInputChange}
                    className="w-full mb-1"
                  />
                  <div className="mb-2">
                    <strong>Responsibilities:</strong>
                    <textarea
                      name="responsibilities"
                      value={modifiedData.responsibilities?.join('\n')}
                      onChange={handleTextAreaChange}
                      className="w-full h-32 border rounded"
                    />
                  </div>
                  <div className="mb-2">
                    <strong>Required Skills:</strong>
                    <textarea
                      name="required_skills"
                      value={modifiedData.required_skills?.join('\n')}
                      onChange={handleTextAreaChange}
                      className="w-full h-32 border rounded"
                    />
                  </div>
                  <div className="flex space-x-4 mt-4">
                    <button
                      onClick={() => handleSave(profile._id)}
                      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={handleCancel}
                      className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <div>
                  <h3 className="text-2xl font-semibold mb-2">
                    {profile.job_title}{" "}
                    {profile.approved && (
                      <span className="text-green-600">(Approved)</span>
                    )}
                  </h3>
                  <p className="text-gray-700 mb-1">
                    <strong>Company:</strong> {profile.company}
                  </p>
                  <p className="text-gray-700 mb-1">
                    <strong>Location:</strong> {profile.location}
                  </p>
                  <p className="text-gray-700 mb-1">
                    <strong>Experience Level:</strong> {profile.experience_level}
                  </p>
                  <p className="text-gray-700 mb-1">
                    <strong>Education:</strong>{" "}
                    {profile.educational_requirements}
                  </p>

                  <div className="mb-2">
                    <strong>Responsibilities:</strong>
                    <ul className="list-disc ml-6">
                      {profile.responsibilities?.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="mb-2">
                    <strong>Required Skills:</strong>
                    <ul className="list-disc ml-6">
                      {profile.required_skills?.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="flex space-x-4 mt-4">
                    <button
                      onClick={() => handleApprove(profile._id)}
                      className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                      disabled={profile.approved}
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleDisapprove(profile._id)}
                      className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                    >
                      Disapprove
                    </button>
                    <button
                      onClick={() => handleModify(profile)}
                      className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
                    >
                      Modify
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
};

export default Profiles;
