
export enum PipelineStage {
  APPLIED = 'Applied',
  SCREENING = 'Screening',
  ASSESSMENT = 'Assessment',
  INTERVIEW = 'Interview',
  OFFER = 'Offer',
  HIRED = 'Hired',
}

export interface Candidate {
  id: string;
  jobId: string;
  name: string;
  avatarUrl: string;
  matchScore: number;
  stage: PipelineStage;
  email: string;
  resumeSummary: string;
  resumeUrl: string | null;
  interviewNotes?: string;
}

export interface Job {
  id: string;
  title: string;
  department: string;
  description: string;
  responsibilities: string[];
  qualifications: string[];
  status: 'Open' | 'Closed';
}

export interface EnhancedJobDescription {
  enhancedTitle: string;
  engagingSummary: string;
  keyResponsibilities: string[];
  requiredQualifications: string[];
}
