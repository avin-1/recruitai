import React from 'react';
import { MenuIcon } from './icons/MenuIcon';

interface HeaderProps {
  onMenuClick: () => void;
  currentView: string;
  breadcrumbs: string[];
}

const viewToTitleMap: { [key: string]: string } = {
  'dashboard': 'Dashboard',
  'job-descriptions': 'Job Descriptions',
  'resume-parsing': 'Resume Parsing',
  'shortlisting': 'Shortlisting',
  'interview-scheduling': 'Interview Scheduling',
  'feedback': 'Feedback Dashboard',
  'other-jobs': 'Other Jobs',
  'contact': 'Contact Info',
};

const Header: React.FC<HeaderProps> = ({ onMenuClick, breadcrumbs }) => {
  const title = viewToTitleMap[breadcrumbs[0]] || 'RecruitAI';

  const renderBreadcrumbs = () => {
    if (breadcrumbs.length > 1) {
      return (
        <>
           <span className="text-slate-500 capitalize">RecruitAI / {breadcrumbs[0]} /</span> {breadcrumbs[1]}
        </>
      )
    }
    return <><span className="text-slate-500">RecruitAI /</span> {title}</>
  }


  return (
    <header className="flex-shrink-0 bg-slate-900 border-b border-slate-700">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
             <button
              onClick={onMenuClick}
              className="lg:hidden mr-4 text-slate-400 hover:text-slate-200"
              aria-label="Open sidebar"
            >
              <MenuIcon className="h-6 w-6" />
            </button>
            <div className="text-sm text-slate-400">
              {renderBreadcrumbs()}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;