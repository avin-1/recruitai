import React from 'react';

const shortlists = [
  {
    jobTitle: 'Senior Frontend Engineer',
    candidates: [
      { name: 'Diana Prince', avatar: 'https://picsum.photos/seed/cand-4/100/100' },
      { name: 'Alice Johnson', avatar: 'https://picsum.photos/seed/cand-1/100/100' },
      { name: 'Bob Williams', avatar: 'https://picsum.photos/seed/cand-2/100/100' },
      { name: 'Charlie Brown', avatar: 'https://picsum.photos/seed/cand-3/100/100' },
    ],
    status: 'Final Review',
  },
  {
    jobTitle: 'UX/UI Designer',
    candidates: [
      { name: 'Heidi Klum', avatar: 'https://picsum.photos/seed/cand-8/100/100' },
      { name: 'George Costanza', avatar: 'https://picsum.photos/seed/cand-7/100/100' },
    ],
    status: 'Interviews Scheduled',
  },
  {
    jobTitle: 'Data Scientist',
    candidates: [
       { name: 'Dana Scully', avatar: 'https://picsum.photos/seed/cand-12/100/100' },
       { name: 'Fox Mulder', avatar: 'https://picsum.photos/seed/cand-13/100/100' },
       { name: 'Walter White', avatar: 'https://picsum.photos/seed/cand-14/100/100' },
    ],
    status: 'Initial Screening',
  }
];

const ShortlistingView: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Candidate Shortlists
      </h2>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {shortlists.map((list) => (
          <div key={list.jobTitle} className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white">{list.jobTitle}</h3>
            <p className="text-sm text-indigo-400 mb-4">{list.status}</p>
            <div className="flex -space-x-2 overflow-hidden">
              {list.candidates.map(c => (
                <img
                  key={c.name}
                  className="inline-block h-10 w-10 rounded-full ring-2 ring-slate-800"
                  src={c.avatar}
                  alt={c.name}
                  title={c.name}
                />
              ))}
            </div>
            <p className="mt-4 text-sm text-slate-400">
              {list.candidates.length} candidates shortlisted for this role.
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ShortlistingView;