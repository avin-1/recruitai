
import { Job, Candidate, PipelineStage } from './types';

export const mockJobs: Job[] = [
  {
    id: 'job-1',
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    description: 'We are looking for a seasoned Frontend Engineer to build and scale our user-facing applications.',
    responsibilities: [
      'Develop and maintain user-facing features using React.js',
      'Build reusable components and front-end libraries for future use',
      'Translate designs and wireframes into high-quality code',
      'Optimize components for maximum performance across a vast array of web-capable devices and browsers',
    ],
    qualifications: [
      'Strong proficiency in JavaScript, including DOM manipulation and the JavaScript object model',
      'Thorough understanding of React.js and its core principles',
      'Experience with popular React.js workflows (such as Flux or Redux)',
      'Familiarity with newer specifications of EcmaScript',
    ],
    status: 'Open',
  },
  {
    id: 'job-2',
    title: 'UX/UI Designer',
    department: 'Design',
    description: 'Seeking a creative UX/UI designer to shape the user experience of our products.',
    responsibilities: [],
    qualifications: [],
    status: 'Open',
  },
  {
    id: 'job-3',
    title: 'Backend Developer (Node.js)',
    department: 'Engineering',
    description: 'Join our backend team to build robust and scalable APIs.',
    responsibilities: [],
    qualifications: [],
    status: 'Closed',
  },
];

export const mockCandidates: Candidate[] = [
  // Candidates for job-1
  { id: 'cand-1', jobId: 'job-1', name: 'Alice Johnson', avatarUrl: 'https://picsum.photos/seed/cand-1/100/100', matchScore: 92, stage: PipelineStage.INTERVIEW, email: 'alice@example.com', resumeSummary: '10+ years of experience in frontend development with expertise in React and performance optimization.', resumeUrl: null },
  { id: 'cand-2', jobId: 'job-1', name: 'Bob Williams', avatarUrl: 'https://picsum.photos/seed/cand-2/100/100', matchScore: 88, stage: PipelineStage.ASSESSMENT, email: 'bob@example.com', resumeSummary: 'Skilled frontend developer with a strong eye for UI/UX and experience in building design systems.', resumeUrl: null },
  { id: 'cand-3', jobId: 'job-1', name: 'Charlie Brown', avatarUrl: 'https://picsum.photos/seed/cand-3/100/100', matchScore: 85, stage: PipelineStage.ASSESSMENT, email: 'charlie@example.com', resumeSummary: 'Full-stack developer with a passion for frontend technologies and creating intuitive user experiences.', resumeUrl: null },
  { id: 'cand-4', jobId: 'job-1', name: 'Diana Prince', avatarUrl: 'https://picsum.photos/seed/cand-4/100/100', matchScore: 95, stage: PipelineStage.OFFER, email: 'diana@example.com', resumeSummary: 'Lead Frontend Engineer with a track record of shipping high-quality products and mentoring junior developers.', resumeUrl: null },
  { id: 'cand-5', jobId: 'job-1', name: 'Ethan Hunt', avatarUrl: 'https://picsum.photos/seed/cand-5/100/100', matchScore: 78, stage: PipelineStage.SCREENING, email: 'ethan@example.com', resumeSummary: 'Recent bootcamp graduate with strong fundamentals in React and a desire to learn.', resumeUrl: null },
  { id: 'cand-6', jobId: 'job-1', name: 'Fiona Glenanne', avatarUrl: 'https://picsum.photos/seed/cand-6/100/100', matchScore: 72, stage: PipelineStage.APPLIED, email: 'fiona@example.com', resumeSummary: 'Software engineer with experience in various languages, looking to specialize in frontend development.', resumeUrl: null },
  { id: 'cand-11', jobId: 'job-1', name: 'Grace Hopper', avatarUrl: 'https://picsum.photos/seed/cand-11/100/100', matchScore: 99, stage: PipelineStage.HIRED, email: 'grace@example.com', resumeSummary: 'Pioneering computer scientist with extensive experience in compiler technology and high-level programming languages.', resumeUrl: null },

  // Candidates for job-2
  { id: 'cand-7', jobId: 'job-2', name: 'George Costanza', avatarUrl: 'https://picsum.photos/seed/cand-7/100/100', matchScore: 89, stage: PipelineStage.INTERVIEW, email: 'george@example.com', resumeSummary: 'UX designer focused on user-centered design principles and creating seamless digital experiences.', resumeUrl: null },
  { id: 'cand-8', jobId: 'job-2', name: 'Heidi Klum', avatarUrl: 'https://picsum.photos/seed/cand-8/100/100', matchScore: 91, stage: PipelineStage.APPLIED, email: 'heidi@example.com', resumeSummary: 'Creative UI designer with a background in graphic design and a portfolio of beautiful mobile and web applications.', resumeUrl: null },

  // Candidates for job-3
  { id: 'cand-9', jobId: 'job-3', name: 'Ian Malcolm', avatarUrl: 'https://picsum.photos/seed/cand-9/100/100', matchScore: 94, stage: PipelineStage.HIRED, email: 'ian@example.com', resumeSummary: 'Expert in chaos theory and backend systems. Proficient in Node.js, microservices, and database architecture.', resumeUrl: null },
  { id: 'cand-10', jobId: 'job-3', name: 'Jane Goodall', avatarUrl: 'https://picsum.photos/seed/cand-10/100/100', matchScore: 82, stage: PipelineStage.HIRED, email: 'jane@example.com', resumeSummary: 'Backend developer with a focus on data integrity and API security.', resumeUrl: null },
];

export const PIPELINE_STAGES = [
  PipelineStage.APPLIED,
  PipelineStage.SCREENING,
  PipelineStage.ASSESSMENT,
  PipelineStage.INTERVIEW,
  PipelineStage.OFFER,
  PipelineStage.HIRED,
];
