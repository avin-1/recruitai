import React, { useEffect, useState } from "react";
import axios from "axios";

const Profiles = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  // Fetch profiles from backend
  const fetchProfiles = async () => {
    try {
      const res = await axios.get("http://localhost:5001/profiles");
      setProfiles(res.data.profiles);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setMessage("❌ Failed to load profiles");
      setLoading(false);
    }
  };

  // Approve profile
  const handleApprove = async (job_title) => {
    try {
      await axios.post(`http://localhost:5001/approve`, { job_title });
      setProfiles(
        profiles.map((p) =>
          p.job_title === job_title ? { ...p, approved: true } : p
        )
      );
      setMessage(`✅ Profile "${job_title}" approved`);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to approve profile "${job_title}"`);
    }
  };

  // Disapprove profile (delete)
  const handleDisapprove = async (job_title) => {
    try {
      await axios.post(`http://localhost:5001/delete`, { job_title });
      setProfiles(profiles.filter((p) => p.job_title !== job_title));
      setMessage(`❌ Profile "${job_title}" deleted`);
    } catch (err) {
      console.error(err);
      setMessage(`❌ Failed to delete profile "${job_title}"`);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, []);

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
              key={profile.job_title}
              className="mb-8 p-6 border rounded-lg shadow-sm"
            >
              <h3 className="text-2xl font-semibold mb-2">{profile.job_title}</h3>
              <p className="text-gray-700 mb-1"><strong>Company:</strong> {profile.company}</p>
              <p className="text-gray-700 mb-1"><strong>Location:</strong> {profile.location}</p>
              <p className="text-gray-700 mb-1"><strong>Experience Level:</strong> {profile.experience_level}</p>
              <p className="text-gray-700 mb-1"><strong>Education:</strong> {profile.educational_requirements}</p>

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
                {profile.approved ? (
                  <button
                    disabled
                    className="bg-gray-400 text-white px-4 py-2 rounded cursor-not-allowed"
                  >
                    Approved
                  </button>
                ) : (
                  <button
                    onClick={() => handleApprove(profile.job_title)}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                  >
                    Approve
                  </button>
                )}
                <button
                  onClick={() => handleDisapprove(profile.job_title)}
                  className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                >
                  Disapprove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
};

export default Profiles;
