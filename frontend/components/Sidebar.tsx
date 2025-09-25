import React from 'react';
import { BriefcaseIcon } from './icons/BriefcaseIcon';
import { LayoutDashboardIcon } from './icons/LayoutDashboardIcon';
import { DocumentTextIcon } from './icons/DocumentTextIcon';
import { UserSearchIcon } from './icons/UserSearchIcon';
import { ClipboardListIcon } from './icons/ClipboardListIcon';
import { CalendarIcon } from './icons/CalendarIcon';
import { ChartPieIcon } from './icons/ChartPieIcon';
import { EnvelopeIcon } from './icons/EnvelopeIcon';

type View = 'dashboard' | 'job-descriptions' | 'resume-parsing' | 'shortlisting' | 'interview-scheduling' | 'feedback' | 'other-jobs' | 'contact';

interface SidebarProps {
  isOpen: boolean;
  setOpen: (isOpen: boolean) => void;
  currentView: View;
  onNavigate: (view: View) => void;
}

const navItems: { name: string; view: View; icon: React.FC<React.SVGProps<SVGSVGElement>> }[] = [
  { name: 'Dashboard', view: 'dashboard', icon: LayoutDashboardIcon },
  { name: 'Job Descriptions', view: 'job-descriptions', icon: DocumentTextIcon },
  { name: 'Resume Parsing', view: 'resume-parsing', icon: UserSearchIcon },
  { name: 'Shortlisting', view: 'shortlisting', icon: ClipboardListIcon },
  { name: 'Interview Scheduling', view: 'interview-scheduling', icon: CalendarIcon },
  { name: 'Feedback Dashboard', view: 'feedback', icon: ChartPieIcon },
  { name: 'Other Jobs', view: 'other-jobs', icon: BriefcaseIcon },
  { name: 'Contact Info', view: 'contact', icon: EnvelopeIcon },
];

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

const SidebarContent: React.FC<{ currentView: View; onNavigate: (view: View) => void; }> = ({ currentView, onNavigate }) => (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6 pb-4">
        <div className="flex h-16 shrink-0 items-center space-x-3">
            <BriefcaseIcon className="h-8 w-8 text-indigo-400" />
            <h1 className="text-xl font-bold text-white">
              RecruitAI
            </h1>
        </div>
        <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
                <li>
                    <ul role="list" className="-mx-2 space-y-1">
                        {navItems.map((item) => (
                            <li key={item.name}>
                                <a
                                    href="#"
                                    onClick={(e) => { e.preventDefault(); onNavigate(item.view); }}
                                    className={classNames(
                                        item.view === currentView
                                            ? 'bg-gray-800 text-white'
                                            : 'text-gray-400 hover:text-white hover:bg-gray-800/50',
                                        'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold'
                                    )}
                                >
                                    <item.icon
                                        className={classNames(
                                            item.view === currentView ? 'text-white' : 'text-gray-500 group-hover:text-white',
                                            'h-6 w-6 shrink-0'
                                        )}
                                        aria-hidden="true"
                                    />
                                    {item.name}
                                </a>
                            </li>
                        ))}
                    </ul>
                </li>
            </ul>
        </nav>
    </div>
);

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setOpen, currentView, onNavigate }) => {
  return (
    <>
      {/* Mobile sidebar */}
      <div className={`relative z-50 lg:hidden ${isOpen ? 'block' : 'hidden'}`} role="dialog" aria-modal="true">
        <div 
          className={`fixed inset-0 bg-gray-900/80 transition-opacity duration-300 ease-linear ${isOpen ? 'opacity-100' : 'opacity-0'}`}
          onClick={() => setOpen(false)}
        ></div>
        <div className="fixed inset-0 flex">
          <div className={`relative mr-16 flex w-full max-w-xs flex-1 transform transition duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <SidebarContent currentView={currentView} onNavigate={onNavigate} />
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:inset-y-0">
        <div className="border-r border-slate-700 w-full h-full">
            <SidebarContent currentView={currentView} onNavigate={onNavigate} />
        </div>
      </div>
    </>
  );
};

export default Sidebar;