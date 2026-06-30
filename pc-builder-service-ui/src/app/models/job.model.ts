export interface JobResponse {
  jobId: string;
  type: string | null;
  status: string;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  duration: number | null;
  componentsUpdated: number;
  error: string | null;
}
