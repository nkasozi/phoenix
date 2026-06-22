import { useTranslate } from "@refinedev/core";
import { showNotification } from "@mantine/notifications";
import { classifierService } from "src/services";
import { normaliseErrorMessage } from "src/utils";

interface SaveClassParams {
	id?: number;
	name: string;
	description: string;
}

interface SaveKeywordConfigParams {
	id?: number;
	class_id: number;
	musts: string;
	nots?: string;
	is_regex?: boolean;
}

interface AddKeywordConfigParams {
	class_id: number;
	musts: string;
	nots: string;
	is_regex: boolean;
}

export function useKeywordClassifierMutations(
	projectId: string,
	classifierId: string
) {
	const translate = useTranslate();

	const saveClass = async (classData: SaveClassParams) => {
		if (classData.id && classData.name) {
			return classifierService.updateClassifierClassData(
				{
					project_id: projectId,
					classifier_id: classifierId,
					class_id: classData.id,
				},
				{
					name: classData.name,
					description: classData.description,
				}
			);
		} else if (classData.name) {
			return classifierService.createClassifierClassData(
				{ project_id: projectId, classifier_id: classifierId },
				{
					name: classData.name,
					description: classData.description,
				}
			);
		}
	};

	const removeClass = async (classId: number) => {
		return classifierService.removeClassifierClassData({
			project_id: projectId,
			classifier_id: classifierId,
			class_id: classId,
		});
	};

	const saveKeywordConfig = async (config: SaveKeywordConfigParams) => {
		if (config.id && config.musts) {
			return classifierService.updateKeywordClassifierConfig(
				{
					project_id: projectId,
					classifier_id: classifierId,
					config_id: config.id,
				},
				{
					class_id: config.class_id,
					musts: config.musts,
					nots: config.nots || "",
					is_regex: config.is_regex || false,
				}
			);
		} else if (config.id && config.musts === "") {
			return classifierService.removeKeywordClassifierConfig({
				project_id: projectId,
				classifier_id: classifierId,
				config_id: config.id,
			});
		} else if (config.musts) {
			return classifierService.createKeywordClassifierConfig(
				{
					project_id: projectId,
					classifier_id: classifierId,
				},
				{
					class_id: config.class_id,
					musts: config.musts,
					nots: config.nots || "",
					is_regex: config.is_regex || false,
				}
			);
		}
	};

	const removeKeywordConfig = async (configId: number) => {
		return classifierService.removeKeywordClassifierConfig({
			project_id: projectId,
			classifier_id: classifierId,
			config_id: configId,
		});
	};

	const addKeywordConfig = async (params: AddKeywordConfigParams) => {
		return classifierService.createKeywordClassifierConfig(
			{
				project_id: projectId,
				classifier_id: classifierId,
			},
			params
		);
	};

	const addClass = async (params: { name: string; description: string }) => {
		return classifierService.createClassifierClassData(
			{ project_id: projectId, classifier_id: classifierId },
			params
		);
	};

	const updateBasicInfo = async (params: {
		name: string;
		description: string;
	}) => {
		return classifierService.updateClassifierBasicData(
			{
				project_id: projectId,
				classifier_id: classifierId,
			},
			params
		);
	};

	const exportCsv = async () => {
		const response = await classifierService.exportKeywordConfigCsv({
			project_id: projectId,
			classifier_id: classifierId,
		});
		const blob = new Blob([response.data], { type: "text/csv" });
		const contentDisposition = response.headers["content-disposition"];
		let filename = `keyword_classifier_export_project_${projectId}_classifier_${classifierId}.csv`;
		if (contentDisposition) {
			const match = contentDisposition.match(/filename=(.+)/);
			if (match) {
				filename = match[1];
			}
		}
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
		return response;
	};

	const notifyError = (error: unknown) => {
		showNotification({
			title: "Error",
			color: "red",
			message: normaliseErrorMessage(error, translate),
		});
	};

	const notifySuccess = (messageKey = "classifiers.success.success") => {
		showNotification({
			title: translate("status.success"),
			message: translate(messageKey),
		});
	};

	return {
		saveClass,
		removeClass,
		saveKeywordConfig,
		removeKeywordConfig,
		addKeywordConfig,
		addClass,
		updateBasicInfo,
		exportCsv,
		notifyError,
		notifySuccess,
	};
}
