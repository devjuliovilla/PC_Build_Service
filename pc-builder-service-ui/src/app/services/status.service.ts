import { inject, Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { StatusResponse } from '../models/status.model';
import { JobResponse } from '../models/job.model';

@Injectable({ providedIn: 'root' })
export class StatusService {
  private api = inject(ApiService);

  getStatus() {
    return this.api.get<StatusResponse>('/status');
  }

  getHealth() {
    return this.api.get<{ status: string }>('/health');
  }

  triggerScraperUpdate(fallback = false, testRun = false) {
    return this.api.post<JobResponse>('/scraper/update', { fallback, test_run: testRun });
  }

  triggerChairsUpdate() {
    return this.api.post<JobResponse>('/scraper/chairs/update');
  }

  getJob(jobId: string) {
    return this.api.get<JobResponse>(`/jobs/${jobId}`);
  }
}
