import React from 'react';
import { CalendarIcon } from '../icons/CalendarIcon';

const upcomingInterviews = [
  {
    date: 'Today, October 26th',
    interviews: [
      { time: '10:00 AM - 10:45 AM', candidate: 'Alice Johnson', job: 'Senior Frontend Engineer', stage: 'Technical Interview', interviewers: ['John Doe', 'Jane Smith'] },
      { time: '02:00 PM - 02:30 PM', candidate: 'George Costanza', job: 'UX/UI Designer', stage: 'Portfolio Review', interviewers: ['Susan Ross'] },
    ],
  },
  {
    date: 'Tomorrow, October 27th',
    interviews: [
      { time: '11:30 AM - 12:00 PM', candidate: 'Diana Prince', job: 'Senior Frontend Engineer', stage: 'Cultural Fit', interviewers: ['HR Team'] },
    ],
  },
  {
    date: 'Monday, October 30th',
    interviews: [
      { time: '09:00 AM - 10:00 AM', candidate: 'Heidi Klum', job: 'UX/UI Designer', stage: 'Initial Screening', interviewers: ['Michael Scott'] },
      { time: '01:00 PM - 01:45 PM', candidate: 'Bob Williams', job: 'Senior Frontend Engineer', stage: 'Technical Interview', interviewers: ['John Doe'] },
    ],
  }
];

const InterviewSchedulingView: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl mb-6">
        Interview Schedule
      </h2>
      <div className="space-y-8">
        {upcomingInterviews.map((day) => (
          <div key={day.date}>
            <h3 className="text-lg font-semibold text-slate-300 flex items-center mb-4">
                <CalendarIcon className="h-5 w-5 mr-2 text-slate-400" />
                {day.date}
            </h3>
            <div className="space-y-4 border-l-2 border-slate-700 ml-2 pl-6">
              {day.interviews.map((interview) => (
                <div key={interview.time + interview.candidate} className="bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-sm hover:border-indigo-500 transition-colors">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="font-semibold text-white">{interview.candidate}</p>
                            <p className="text-sm text-slate-400">{interview.job}</p>
                        </div>
                        <div className="text-right">
                             <p className="text-sm font-medium text-slate-300">{interview.time}</p>
                             <span className="mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400">{interview.stage}</span>
                        </div>
                    </div>
                  <div className="mt-3 pt-3 border-t border-slate-700/50">
                     <p className="text-sm text-slate-400">Interviewers: <span className="text-slate-300">{interview.interviewers.join(', ')}</span></p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default InterviewSchedulingView;