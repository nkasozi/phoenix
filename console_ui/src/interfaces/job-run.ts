export interface IJobRun {
	project_id: number;
	id?: number;
	type?: string;
}

export interface JobRunResponse {
	foreign_id: number;
	foreign_job_type: string;
	id: number;
	created_at: string;
	updated_at: string;
	project_id: number;
	status: string;
	started_processing_at: string;
	completed_at: string;
	flow_run_id: string;
	flow_run_name: string;
	total_cost: number;
	is_total_cost_estimated: boolean;
	gather_result_count: number;
	gather_normalise_error_count: number;
}
