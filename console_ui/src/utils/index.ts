import { Author } from "@pages/projects/[projectid]/classifiers/manual_post_authors/model";
import { JobRunResponse } from "src/interfaces/job-run";

/**
 * Formats the given date string into a human-readable date format.
 * @param {string} date - The date string to be formatted.
 * @returns {string} A human-readable representation of the date.
 */
export const toReadableDate = (date: string): string => {
	const fd = new Date(date);
	return fd.toDateString();
};

export const statusTextStyle = (type: any): string => {
	switch (type) {
		case "awaiting_start":
			return "text-orange-500";
		case "in_queue":
			return "text-orange-500";
		case "processing":
			return "text-orange-500";
		case "failed":
			return "text-red-500";
		case "completed_successfully":
			return "text-green-500";
		default:
			return "text-neutral-500";
	}
};

export const isJobRunRunning = (jobRun: JobRunResponse | null): boolean =>
	jobRun !== null && !jobRun?.completed_at;

export const formatNumber = (value: number | string): string => {
	let numberValue: number;

	if (typeof value === "string") {
		numberValue = parseFloat(value);
	} else {
		numberValue = value;
	}

	// Check if the value is a valid number
	if (Number.isNaN(numberValue)) {
		return "0";
	}
	if (!numberValue) {
		return "0";
	}

	return numberValue.toLocaleString("en-US", {
		style: "decimal",
		minimumFractionDigits: 0,
		maximumFractionDigits: 2,
	});
};

export const PHEONIX_MANUAL_URL =
	"https://docs.google.com/document/d/1Rs3WYgvkAtZJ9y1ho68AnGfC8mDuOFE9aG52bkJSG24/edit";

export const getAuthorProfileLink = (author: Author): string => {
	if (author?.pi_author_link) {
		return author.pi_author_link;
	}
	if (author?.platform?.toLowerCase() === "facebook") {
		return `https://www.facebook.com/${author?.pi_platform_message_author_id}`;
	}
	if (author?.platform?.toLowerCase() === "tiktok") {
		return `https://www.tiktok.com/@${author.pi_platform_message_author_name}`;
	}
	if (
		author?.platform?.toLowerCase() === "x" ||
		author?.platform?.toLowerCase() === "twitter"
	) {
		return `https://www.x.com/${author.pi_platform_message_author_name}`;
	}
	return "#";
};

export const normaliseErrorMessage = (error: any, translate: any): string => {
	let default_error_message = "An error occurred";
	if (translate) {
		default_error_message = translate("errors.default");
	}

	if (error?.response?.data?.detail) {
		const { detail } = error.response.data;

		if (Array.isArray(detail)) {
			// Extract the 'msg' field from each error detail
			const messages = detail.map((d) => d.msg).join(", ");
			return messages || default_error_message;
		}
		if (typeof detail === "string") {
			return detail;
		}
		return JSON.stringify(detail);
	}
	return default_error_message;
};

export const projectHasRemainingCredits = (project: any): boolean => {
	if (project?.has_unlimited_credits) {
		return true;
	}
	return project?.total_costs < project?.total_allocated_credits;
};

const DEFAULT_ESTIMATED_USAGE_FACTOR = 0.95;
export const MAX_MANUAL_UPLOAD_FILE_SIZE = 1024 * 1024 * 1024;

const gatherEsimateWithErrorMargin = (gather: any): number => {
	const gatherMaxCost = gather?.job_run_resource_estimate?.max_total_cost || 0;
	const errorMargin = Number(
		process.env.NEXT_PUBLIC_GATHER_COST_ESTIMATE_ERROR_MARGIN ||
			DEFAULT_ESTIMATED_USAGE_FACTOR
	);
	return gatherMaxCost * errorMargin;
};

const areCostsGreaterThanAllocatedCredits = (
	costs: number,
	gather: any,
	project: any
): boolean => {
	const totalAllocatedCredits = project?.total_allocated_credits || 0;
	const gatherEstimate = gatherEsimateWithErrorMargin(gather);
	return costs + gatherEstimate > totalAllocatedCredits;
};

export const gatherJobRunEstimateToBig = (
	project: any,
	gather: any
): boolean => {
	if (project?.has_unlimited_credits) {
		return false;
	}
	const totalCosts = project?.total_costs || 0;
	return areCostsGreaterThanAllocatedCredits(totalCosts, gather, project);
};

export const gatherJobRunEstimateToBigWithRunningJobs = (
	project: any,
	gather: any
): boolean => {
	if (project?.has_unlimited_credits) {
		return false;
	}
	const totalCosts = project?.estimated_total_costs || 0;
	return areCostsGreaterThanAllocatedCredits(totalCosts, gather, project);
};

export const formatMaxCreditAfterRun = (project: any, gather: any) => {
	if (gather?.job_run_resource_estimate?.max_gather_result_count) {
		const jobRunStatus = project?.latest_job_run?.status;
		const totalCost = project?.total_costs || 0;
		const gatherMaxTotalCost =
			gather.job_run_resource_estimate.max_total_cost || 0;
		const totalAllocatedCredits = project?.total_allocated_credits || 0;

		return `${jobRunStatus !== "completed_successfully" ? (gatherMaxTotalCost + totalCost).toFixed(3) : totalCost.toFixed(3)} / ${totalAllocatedCredits}`;
	}
	return "?";
};

export const isValidUrl = (url: string) => {
	try {
		const _ = new URL(url);
		return true;
	} catch {
		return false;
	}
};
