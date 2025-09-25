import React from 'react';

const otherJobs = [
  { id: 1, title: 'Product Manager', department: 'Product', status: 'Open' },
  { id: 2, title: 'Data Scientist', department: 'Data Science', status: 'Open' },
  { id: 3, title: 'Marketing Specialist', department: 'Marketing', status: 'Closed' },
  { id: 4, title: 'IT Support Engineer', department: 'IT', status: 'On Hold' },
];

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
  const statusClasses = {
    Open: 'bg-green-100/10 text-green-400',
    Closed: 'bg-slate-100/10 text-slate-400',
    'On Hold': 'bg-yellow-100/10 text-yellow-400',
  };
  return <span className={`${baseClasses} ${statusClasses[status as keyof typeof statusClasses]}`}>{status}</span>;
}

const OtherJobsView: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Other Job Postings
      </h2>
       <div className="overflow-x-auto bg-slate-800 border border-slate-700 rounded-lg shadow-md">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-800">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Job Title</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Department</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-slate-800 divide-y divide-slate-700">
            {otherJobs.map((job) => (
              <tr key={job.id} className="hover:bg-slate-700/50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{job.title}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-400">{job.department}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <StatusBadge status={job.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OtherJobsView;