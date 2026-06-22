"use client";

import { TextInput, Button, ActionIcon, Space, Alert } from "@mantine/core";
import { IconArrowLeft, IconDeviceFloppy } from "@tabler/icons-react";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBack, useTranslate } from "@refinedev/core";
import { classifierService } from "src/services";
import { showNotification } from "@mantine/notifications";
import PerspectiveApiSwitchGroup, {
	perspectiveApiSwitches,
} from "@components/classifier/perspective-api-switch-group";
import PerspectiveApiHeader from "@components/classifier/perspective-api-header";

const CreatePerspectiveApiClassifier: React.FC = () => {
	const back = useBack();
	const router = useRouter();
	const translate = useTranslate();
	const { projectid } = useParams();
	const [loading, setLoading] = useState(false);
	const [formValues, setFormValues] = useState<any>({
		name: "",
		description: "",
		toxicity: false,
		severe_toxicity: false,
		identity_attack: false,
		insult: false,
		sexually_explicit: false,
		flirtation: false,
		threat: false,
	});

	// Input change handlers
	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const { name, value } = e.target;
		setFormValues((prev: any) => ({ ...prev, [name]: value }));
	};

	const handleSwitchChange = (name: string) => {
		setFormValues((prev: any) => ({ ...prev, [name]: !prev[name] }));
	};

	const handleSave = async (): Promise<void> => {
		setLoading(true);
		try {
			const params = perspectiveApiSwitches.reduce((acc: any, curr) => {
				acc[curr.name] = {
					enabled: formValues[curr.name],
				};
				return acc;
			}, {});
			const res = await classifierService.createPerspectiveApiClassifier(
				{
					project_id: projectid,
				},
				{
					name: formValues.name,
					description: formValues.description,
					latest_version: {
						classes: [],
						params,
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
			showNotification({
				title: translate("status.error"),
				color: "red",
				message: error?.response?.data?.message || "An Error Occured",
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
				{translate("classifiers.types.perspective_api.create_page.title")}
			</h1>
			<PerspectiveApiHeader />
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
			</div>
			<Space h="lg" />
			<PerspectiveApiSwitchGroup
				formValues={formValues}
				onSwitchChange={handleSwitchChange}
			/>
			<Space h="lg" />
			<Alert mt="lg" title={translate("note")} color="gray">
				{translate("classifiers.types.perspective_api.warnings.create")}
			</Alert>
			<Space h="lg" />
			<div className="flex justify-end gap-2 w-full">
				<Button
					leftIcon={<IconDeviceFloppy size={16} />}
					mt="sm"
					// fullWidth
					loading={loading}
					disabled={!formValues.name}
					onClick={handleSave}
				>
					{translate("buttons.create_apply")}
				</Button>
			</div>
		</div>
	);
};

export default CreatePerspectiveApiClassifier;
