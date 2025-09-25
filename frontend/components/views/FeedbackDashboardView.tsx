import React from 'react';
import { ChartPieIcon } from '../icons/ChartPieIcon';
import { UsersIcon } from '../icons/UsersIcon';

const stats = [
  { name: 'Open Positions', value: '3' },
  { name: 'Total Candidates', value: '11' },
  { name: 'Avg. Time to Hire', value: '28 Days' },
  { name: 'Offer Acceptance Rate', value: '89%' },
];

const pipelineFunnel = [
    { stage: 'Applied', count: 152, color: 'bg-sky-500' },
    { stage: 'Screening', count: 98, color: 'bg-blue-500' },
    { stage: 'Assessment', count: 45, color: 'bg-purple-500' },
    { stage: 'Interview', count: 22, color: 'bg-indigo-500' },
    { stage: 'Offer', count: 5, color: 'bg-amber-500' },
    { stage: 'Hired', count: 3, color: 'bg-green-500' },
];

const recentFeedback = [
    { candidate: 'Alice Johnson', interviewer: 'John Doe', comment: 'Strong technical skills in React, excellent problem-solver. A bit hesitant on system design questions but demonstrated solid fundamentals. Recommend for next round.' },
    { candidate: 'George Costanza', interviewer: 'Susan Ross', comment: 'Great portfolio, very articulate about their design process. Showed a deep understanding of user-centric design. Would be a great fit for the team.' },
    { candidate: 'Bob Williams', interviewer: 'Jane Smith', comment: 'Good communication skills but seemed to struggle with the live coding exercise. May need more experience with complex state management.' },
];

const FeedbackDashboardView: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Feedback & Analytics Dashboard
      </h2>
      
      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((item) => (
          <div key={item.name} className="overflow-hidden rounded-lg bg-slate-800 border border-slate-700 px-4 py-5 shadow sm:p-6">
            <dt className="truncate text-sm font-medium text-slate-400">{item.name}</dt>
            <dd className="mt-1 text-3xl font-semibold tracking-tight text-white">{item.value}</dd>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Pipeline Funnel */}
        <div className="lg:col-span-1 bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <ChartPieIcon className="h-6 w-6 mr-2 text-indigo-400" />
            Candidate Pipeline Funnel
          </h3>
          <div className="space-y-2">
            {pipelineFunnel.map((item, index) => (
                <div key={item.stage} className="flex items-center">
                    <div className="w-20 text-sm text-slate-400">{item.stage}</div>
                    <div className="flex-1 bg-slate-700 rounded-full h-6">
                        <div 
                            className={`${item.color} h-6 rounded-full flex items-center justify-between px-2`}
                            style={{ width: `${(item.count / pipelineFunnel[0].count) * 100}%` }}
                        >
                           <span className="text-xs font-bold text-white">{item.count}</span>
                        </div>
                    </div>
                </div>
            ))}
          </div>
        </div>

        {/* Recent Feedback */}
        <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <UsersIcon className="h-6 w-6 mr-2 text-indigo-400" />
            Recent Interviewer Feedback
          </h3>
          <div className="space-y-4">
            {recentFeedback.map((fb, index) => (
                <div key={index} className="border-b border-slate-700 pb-3 last:border-b-0 last:pb-0">
                    <p className="text-sm text-slate-300 italic">"{fb.comment}"</p>
                    <p className="text-right text-xs text-slate-400 mt-2">- <span className="font-semibold text-slate-200">{fb.interviewer}</span> on {fb.candidate}</p>
                </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeedbackDashboardView;