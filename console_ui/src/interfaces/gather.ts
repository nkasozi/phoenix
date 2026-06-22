import { JobRunResponse } from "./job-run";

export interface GatherResponse {
	name: string;
	id: number;
	child_type: string;
	created_at: string;
	updated_at: string;
	project_id: number;
	latest_job_run: JobRunResponse;
	delete_job_run: JobRunResponse;
}

export interface IGatherRun {
	id: number;
	project_id: number;
}
