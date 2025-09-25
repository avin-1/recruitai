import React from 'react';

const parsedCandidates = [
  { id: 1, name: 'Alice Johnson', job: 'Senior Frontend Engineer', score: 92, status: 'Completed', skills: ['React', 'TypeScript', 'Redux', 'Jest'] },
  { id: 2, name: 'Bob Williams', job: 'Senior Frontend Engineer', score: 88, status: 'Completed', skills: ['Vue.js', 'UI/UX', 'Figma', 'CSS-in-JS'] },
  { id: 3, name: 'George Costanza', job: 'UX/UI Designer', score: 89, status: 'Completed', skills: ['User Research', 'Wireframing', 'Prototyping'] },
  { id: 4, name: 'Heidi Klum', job: 'UX/UI Designer', score: 91, status: 'Pending', skills: [] },
  { id: 5, name: 'Ethan Hunt', job: 'Senior Frontend Engineer', score: 78, status: 'Error', skills: [] },
  { id: 6, name: 'Fiona Glenanne', job: 'Senior Frontend Engineer', score: 72, status: 'Completed', skills: ['Angular', 'NgRx', 'CI/CD'] },
];

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
  const statusClasses = {
    Completed: 'bg-green-100/10 text-green-400',
    Pending: 'bg-yellow-100/10 text-yellow-400',
    Error: 'bg-red-100/10 text-red-400',
  };
  return <span className={`${baseClasses} ${statusClasses[status as keyof typeof statusClasses]}`}>{status}</span>;
}

const ResumeParsingView: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Resume Parsing Queue
      </h2>
      <div className="overflow-x-auto bg-slate-800 border border-slate-700 rounded-lg shadow-md">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-800">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Candidate</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Job Applied For</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Match Score</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Extracted Skills</th>
            </tr>
          </thead>
          <tbody className="bg-slate-800 divide-y divide-slate-700">
            {parsedCandidates.map((candidate) => (
              <tr key={candidate.id} className="hover:bg-slate-700/50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{candidate.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{candidate.job}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{candidate.score}%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <StatusBadge status={candidate.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">
                  <div className="flex flex-wrap gap-1">
                    {candidate.skills.length > 0 ? candidate.skills.map(skill => (
                      <span key={skill} className="px-2 py-1 text-xs rounded-full bg-indigo-500/10 text-indigo-400">{skill}</span>
                    )) : 'N/A'}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResumeParsingView;