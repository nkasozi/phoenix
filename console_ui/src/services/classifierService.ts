import axios from "@providers/data-provider/axios";
import {
	AddClassToAuthorPayload,
	ClassifierClassPayload,
	ClassifierPayload,
	HuggingFaceClassifierPayload,
	IClassifierArchiveRestore,
	PerspectiveApiClassifierPayload,
	PerspectiveApiLatestVersionPayload,
} from "src/interfaces/classifier";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default class ClassifierService {
	async archiveClassifier(data: IClassifierArchiveRestore) {
		const response = await axios.post(
			`${API_URL}/projects/${data?.project_id}/classifiers/${data?.id}/archive`
		);
		return response;
	}

	async restoreClassifier(data: IClassifierArchiveRestore) {
		const response = await axios.post(
			`${API_URL}/projects/${data?.project_id}/classifiers/${data?.id}/restore`
		);
		return response;
	}

	async getClassifierData(params: {
		project_id: string;
		classifier_id: string;
	}) {
		const response = await axios.get(
			`${API_URL}/projects/${params?.project_id}/classifiers/${params?.classifier_id}`
		);
		return response;
	}

	async runKeywordClassifier(params: any) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/keyword_match/${params?.classifier_id}/version_and_run`
		);
		return response;
	}

	async runManualPostAuthorsClassifier(params: any) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/manual_post_authors/${params?.classifier_id}/version_and_run`
		);
		return response;
	}

	async updateClassifierBasicData(params: any, data: ClassifierPayload) {
		const response = await axios.patch(
			`${API_URL}/projects/${params?.project_id}/classifiers/${params?.classifier_id}`,
			data
		);
		return response;
	}

	async createKeywordClassifier(params: any, data: ClassifierPayload) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/keyword_match`,
			data
		);
		return response;
	}

	async createClassifierClassData(params: any, data: ClassifierClassPayload) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/${params?.classifier_id}/intermediatory_classes`,
			data
		);
		return response;
	}

	async updateClassifierClassData(params: any, data: ClassifierClassPayload) {
		const response = await axios.patch(
			`${API_URL}/projects/${params?.project_id}/classifiers/${params?.classifier_id}/intermediatory_classes/${params?.class_id}`,
			data
		);
		return response;
	}

	async removeClassifierClassData(params: any) {
		const response = await axios.delete(
			`${API_URL}/projects/${params?.project_id}/classifiers/${params?.classifier_id}/intermediatory_classes/${params?.class_id}`
		);
		return response;
	}

	async createKeywordClassifierConfig(
		params: any,
		data: { class_id: number; musts: string; nots: string; is_regex?: boolean }
	) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/keyword_match/${params?.classifier_id}/intermediatory_class_to_keyword_configs`,
			data
		);
		return response;
	}

	async updateKeywordClassifierConfig(
		params: any,
		data: { class_id: number; musts: string; nots: string; is_regex?: boolean }
	) {
		const response = await axios.put(
			`${API_URL}/projects/${params?.project_id}/classifiers/keyword_match/${params?.classifier_id}/intermediatory_class_to_keyword_configs/${params?.config_id}`,
			data
		);
		return response;
	}

	async removeKeywordClassifierConfig(params: any) {
		const response = await axios.delete(
			`${API_URL}/projects/${params?.project_id}/classifiers/keyword_match/${params?.classifier_id}/intermediatory_class_to_keyword_configs/${params?.config_id}`
		);
		return response;
	}

	// Manual Post Authors
	async createManualPostClassifier(params: any, data: ClassifierPayload) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/manual_post_authors`,
			data
		);
		return response;
	}

	async getManualPostAuthors(query: {
		project_id: string;
		classifier_id: string;
		params: {
			start: number;
			end: number;
		};
	}) {
		const response = await axios.get(
			`${API_URL}/projects/${query?.project_id}/classifiers/manual_post_authors/${query?.classifier_id}/authors?start=${query.params.start}&end=${query.params.end}`
		);
		return response;
	}

	async getManualPostAuthorById(query: {
		project_id: string;
		classifier_id: string;
		id: string;
	}) {
		const response = await axios.get(
			`${API_URL}/projects/${query?.project_id}/classifiers/manual_post_authors/${query?.classifier_id}/authors/${query.id}`
		);
		return response;
	}

	async getRefreshManualPostAuthors(query: {
		project_id: string;
		params: {
			start: number;
			end: number;
		};
	}) {
		const response = await axios.get(
			`${API_URL}/projects/${query?.project_id}/classifiers/manual_post_authors/authors?start=${query.params.start}&end=${query.params.end}`
		);
		return response;
	}

	async addClassToManualPostAuthorClassifier(
		params: any,
		data: AddClassToAuthorPayload
	) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/manual_post_authors/${params?.classifier_id}/intermediatory_author_classes`,
			data
		);
		return response;
	}

	async removeClassToManualPostAuthorClassifier(params: any) {
		const response = await axios.delete(
			`${API_URL}/projects/${params?.project_id}/classifiers/manual_post_authors/${params?.classifier_id}/intermediatory_author_classes/${params?.classified_post_author_id}`
		);
		return response;
	}

	// Perspective API
	async createPerspectiveApiClassifier(
		params: any,
		data: PerspectiveApiClassifierPayload
	) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/perspective_api`,
			data
		);
		return response;
	}

	async updatePerspectiveApiClassifier(
		params: any,
		data: PerspectiveApiLatestVersionPayload
	) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/perspective_api/${params?.classifier_id}/version_and_run`,
			data
		);
		return response;
	}

	// Keyword Match CSV Export
	async exportKeywordConfigCsv(params: {
		project_id: string;
		classifier_id: string;
	}) {
		const response = await axios.get(
			`${API_URL}/projects/${params.project_id}/classifiers/keyword_match/${params.classifier_id}/export_csv`,
			{ responseType: "blob" }
		);
		return response;
	}

	// Keyword Match CSV Import
	async importKeywordConfigCsv(
		params: { project_id: string; classifier_id: string },
		file: File,
		importMode: string
	) {
		const formData = new FormData();
		formData.append("file", file);
		const response = await axios.post(
			`${API_URL}/projects/${params.project_id}/classifiers/keyword_match/${params.classifier_id}/import_csv?import_mode=${importMode}`,
			formData,
			{ headers: { "Content-Type": "multipart/form-data" } }
		);
		return response;
	}

	// Hugging Face Classifier
	async createHuggingFaceClassifier(
		params: any,
		data: HuggingFaceClassifierPayload
	) {
		const response = await axios.post(
			`${API_URL}/projects/${params?.project_id}/classifiers/hugging_face`,
			data
		);
		return response;
	}
}
