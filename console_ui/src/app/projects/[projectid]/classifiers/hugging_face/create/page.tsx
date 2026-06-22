"use client";

import { TextInput, Button, ActionIcon, Space, Alert } from "@mantine/core";
import {
	IconArrowLeft,
	IconDeviceFloppy,
	IconAlertCircle,
} from "@tabler/icons-react";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBack, useTranslate } from "@refinedev/core";
import { classifierService } from "src/services";
import { showNotification } from "@mantine/notifications";
import HuggingFaceClassifierHeader from "@components/classifier/hugging-face-header";

const CreateHiggingFaceClassifier: React.FC = () => {
	const back = useBack();
	const router = useRouter();
	const translate = useTranslate();
	const { projectid } = useParams();
	const [loading, setLoading] = useState(false);
	const [errorKey, setErrorKey] = useState<string>("");
	const [formValues, setFormValues] = useState<any>({
		name: "",
		description: "",
		model_id: "",
	});

	// Function to strip Hugging Face URL prefix
	const stripHuggingFaceUrl = (value: string): string => {
		const huggingFacePrefix = "https://huggingface.co/";
		if (value.startsWith(huggingFacePrefix)) {
			return value.substring(huggingFacePrefix.length);
		}
		return value;
	};

	// Input change handlers
	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const { name, value } = e.target;

		// Special handling for model_id to strip Hugging Face URL
		if (name === "model_id") {
			const strippedValue = stripHuggingFaceUrl(value);
			setFormValues((prev: any) => ({ ...prev, [name]: strippedValue }));
		} else {
			setFormValues((prev: any) => ({ ...prev, [name]: value }));
		}
	};

	const handleSave = async (): Promise<void> => {
		setLoading(true);
		setErrorKey(""); // Clear any existing error message

		try {
			const res = await classifierService.createHuggingFaceClassifier(
				{
					project_id: projectid,
				},
				{
					name: formValues.name,
					description: formValues.description,
					latest_version: {
						params: {
							model_id: formValues.model_id,
						},
					},
				}
			);
			const { data } = res;
			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.success"),
			});
			router.push(
				`/projects/${projectid}/classifiers/${data?.type}/${data.id}`
			);
		} catch (error: any) {
			// Extract error key from response
			setErrorKey(error?.response?.data?.detail?.error_key);

			// Also show notification for immediate feedback
			showNotification({
				title: translate("status.error"),
				color: "red",
				message: error?.response?.data?.message || "An Error Occurred",
			});
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="p-8 bg-white min-h-screen">
			<h1 className="flex items-center gap-2 text-2xl font-semibold">
				<ActionIcon onClick={back}>
					<IconArrowLeft />
				</ActionIcon>
				{translate("classifiers.types.hugging_face.create_page.title")}
			</h1>
			<HuggingFaceClassifierHeader />
			<Space h="md" />
			<div>
				<TextInput
					name="name"
					label={translate("projects.fields.name")}
					placeholder={translate("classifiers.fields.name_placeholder")}
					value={formValues.name}
					onChange={handleInputChange}
					required
				/>
				<Space h="sm" />
				<TextInput
					name="description"
					label={translate("projects.fields.description")}
					placeholder={translate("classifiers.fields.description_placeholder")}
					value={formValues.description}
					onChange={handleInputChange}
					required
				/>
				<Space h="sm" />
				<TextInput
					name="model_id"
					label={translate("classifiers.types.hugging_face.input.hub_url")}
					placeholder={translate(
						"classifiers.types.hugging_face.input.hub_url_placeholder"
					)}
					value={formValues.model_id}
					onChange={handleInputChange}
					required
				/>
			</div>
			<Space h="lg" />

			{/* Error Message Display */}
			{errorKey && (
				<Alert
					icon={<IconAlertCircle size={16} />}
					title={translate("status.error") || "Error"}
					color="red"
					variant="light"
					mb="md"
				>
					{translate(`classifiers.types.hugging_face.errors.${errorKey}`) ||
						translate("classifiers.errors.generic")}
				</Alert>
			)}

			<div className="flex justify-end gap-2 w-full">
				<Button
					leftIcon={<IconDeviceFloppy size={16} />}
					mt="sm"
					loading={loading}
					disabled={!formValues.name || !formValues.model_id}
					onClick={handleSave}
				>
					{translate("buttons.create_apply")}
				</Button>
			</div>
		</div>
	);
};

export default CreateHiggingFaceClassifier;
