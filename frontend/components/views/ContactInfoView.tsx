import React from 'react';
import { EnvelopeIcon } from '../icons/EnvelopeIcon';

const hrTeam = [
    { name: 'Michael Scott', role: 'Regional Manager, HR', email: 'michael.scott@dundermifflin.com' },
    { name: 'Holly Flax', role: 'HR Representative', email: 'holly.flax@dundermifflin.com' },
    { name: 'Toby Flenderson', role: 'HR Representative (Scranton)', email: 'toby.flenderson@dundermifflin.com' }
]

const ContactInfoView: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-full">
        <div className="w-full max-w-2xl">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 shadow-lg">
                <div className="text-center">
                    <EnvelopeIcon className="mx-auto h-12 w-12 text-indigo-400"/>
                    <h2 className="mt-4 text-2xl font-bold text-white">
                        Contact Human Resources
                    </h2>
                    <p className="mt-2 text-slate-400">
                        For any inquiries regarding job postings, applications, or the recruitment process, please reach out to our team.
                    </p>
                </div>

                <div className="mt-8 border-t border-slate-700 pt-8">
                    <dl className="space-y-6">
                       {hrTeam.map(person => (
                         <div key={person.name} className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                                <img className="h-10 w-10 rounded-full" src={`https://i.pravatar.cc/100?u=${person.email}`} alt={person.name} />
                            </div>
                            <div>
                                <dt className="text-sm font-semibold text-white">{person.name}</dt>
                                <dd className="text-sm text-slate-400">{person.role}</dd>
                                <dd className="mt-1 text-sm text-indigo-400 hover:text-indigo-300">
                                    <a href={`mailto:${person.email}`}>{person.email}</a>
                                </dd>
                            </div>
                         </div>
                       ))}
                    </dl>
                </div>
            </div>
        </div>
    </div>
  );
};

export default ContactInfoView;