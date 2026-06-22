import { JobRunResponse } from "./job-run";

export interface IClassifierArchiveRestore {
	project_id: number;
	id?: number;
}

export interface ClassifierResponse {
	name: string;
	id: number;
	archived_at: string;
	type: string;
	last_edited_at: string;
	created_at: string;
	updated_at: string;
	project_id: number;
	latest_job_run: JobRunResponse;
	latest_version: {
		classes: any;
		classifier_id: number;
		created_at: string;
		params: any;
		updated_at: string;
		version_id: number;
	};
}

export interface ClassifierPayload {
	name: string;
	description: string;
	intermediatory_classes?: ClassifierClassPayload[];
}

export interface ClassifierClassPayload {
	name: string;
	description: string;
}

export interface AddClassToAuthorPayload {
	class_id: number;
	phoenix_platform_message_author_id: string;
}

export interface PerspectiveApiClassifierPayload {
	name?: string;
	description?: string;
	latest_version: PerspectiveApiLatestVersionPayload;
}

export interface PerspectiveApiLatestVersionPayload {
	classes: [];
	params: {
		toxicity: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		severe_toxicity: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		identity_attack: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		insult: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		threat: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		sexually_explicit: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
		flirtation: {
			enabled: boolean;
			buckets?: {
				name: string;
				upper_threshold: number;
			}[];
		};
	};
}

export interface HuggingFaceClassifierPayload {
	name?: string;
	description?: string;
	latest_version: HuggingFaceClassifierLatestVersionPayload;
}

export interface HuggingFaceClassifierLatestVersionPayload {
	params: {
		model_id: string;
	};
}
