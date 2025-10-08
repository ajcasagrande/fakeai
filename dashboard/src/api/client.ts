import axios, { AxiosInstance } from 'axios';
import type {
  FineTuningJob,
  FineTuningJobList,
  FineTuningJobRequest,
  FineTuningEventList,
  FineTuningCheckpointList,
} from '../types/fine-tuning';

class FineTuningAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = '/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async createJob(request: FineTuningJobRequest): Promise<FineTuningJob> {
    const response = await this.client.post<FineTuningJob>(
      '/fine_tuning/jobs',
      request
    );
    return response.data;
  }

  async listJobs(limit: number = 20, after?: string): Promise<FineTuningJobList> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    const url = '/fine_tuning/jobs?' + params.toString();
    const response = await this.client.get<FineTuningJobList>(url);
    return response.data;
  }

  async getJob(jobId: string): Promise<FineTuningJob> {
    const response = await this.client.get<FineTuningJob>(
      '/fine_tuning/jobs/' + jobId
    );
    return response.data;
  }

  async cancelJob(jobId: string): Promise<FineTuningJob> {
    const response = await this.client.post<FineTuningJob>(
      '/fine_tuning/jobs/' + jobId + '/cancel'
    );
    return response.data;
  }

  async getEvents(jobId: string, limit: number = 20): Promise<FineTuningEventList> {
    const response = await this.client.get<FineTuningEventList>(
      '/fine_tuning/jobs/' + jobId + '/events?limit=' + limit
    );
    return response.data;
  }

  async getCheckpoints(jobId: string, limit: number = 10): Promise<FineTuningCheckpointList> {
    const response = await this.client.get<FineTuningCheckpointList>(
      '/fine_tuning/jobs/' + jobId + '/checkpoints?limit=' + limit
    );
    return response.data;
  }

  createEventStream(jobId: string): EventSource {
    return new EventSource('/v1/fine_tuning/jobs/' + jobId + '/events');
  }
}

export const fineTuningAPI = new FineTuningAPI();
export default fineTuningAPI;
