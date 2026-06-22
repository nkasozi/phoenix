import axios from "@providers/data-provider/axios";
import { IJobRun } from "src/interfaces/job-run";
import { IGatherRun } from "src/interfaces/gather";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default class GatherService {
	async run(data: IGatherRun) {
		const response = await axios.post(
			`${API_URL}/projects/${data?.project_id}/gathers/${data?.id}/run`
		);
		return response;
	}

	async gatherList(projectid: string) {
		const response = await axios.get(
			`${API_URL}/projects/${projectid}/gathers`
		);
		return response;
	}

	async getGatherRunEstimate(data: IJobRun) {
		const response = await axios.get(
			`${API_URL}/projects/${data?.project_id}/gathers/${data?.id}/estimate`
		);
		return response;
	}

	async deleteGather(data: IJobRun) {
		const response = await axios.delete(
			`${API_URL}/projects/${data?.project_id}/gathers/${data?.id}`
		);
		return response;
	}
}
