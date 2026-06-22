"use client";

import { TextInput, Button, Space, Divider, Alert } from "@mantine/core";
import { IconCheck, IconDeviceFloppy } from "@tabler/icons-react";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslate } from "@refinedev/core";
import { classifierService } from "src/services";
import { showNotification } from "@mantine/notifications";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import PerspectiveApiSwitchGroup, {
	perspectiveApiSwitches,
} from "@components/classifier/perspective-api-switch-group";
import PerspectiveApiHeader from "@components/classifier/perspective-api-header";

const EditPerspectiveApiClassifier: React.FC = () => {
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	const [loading, setLoading] = useState(false);
	const [classifierName, setClassifierName] = useState("");
	const [classifierDescription, setClassifierDescription] = useState("");
	const [classifier, setClassifier] = useState<any>();
	const [formValues, setFormValues] = useState<any>({
		toxicity: false,
		severe_toxicity: false,
		identity_attack: false,
		insult: false,
		sexually_explicit: false,
		flirtation: false,
		threat: false,
	});
	const [isModified, setIsModified] = useState<boolean>(false);
	const [isBasicModified, setIsBasicModified] = useState<boolean>(false);

	const handleSwitchChange = (name: string) => {
		setFormValues((prev: any) => ({ ...prev, [name]: !prev[name] }));
		setIsModified(true);
	};

	const fetchData = useCallback(async () => {
		try {
			const response = await classifierService.getClassifierData({
				project_id: projectid as string,
				classifier_id: id as string,
			});
			const { data } = response;
			setClassifier(data);
			setClassifierName(data?.name);
			setClassifierDescription(data?.description);
			setFormValues({
				toxicity: data?.latest_version?.params?.toxicity?.enabled,
				severe_toxicity: data?.latest_version?.params?.severe_toxicity?.enabled,
				identity_attack: data?.latest_version?.params?.identity_attack?.enabled,
				insult: data?.latest_version?.params?.insult?.enabled,
				sexually_explicit:
					data?.latest_version?.params?.sexually_explicit?.enabled,
				flirtation: data?.latest_version?.params?.flirtation?.enabled,
				threat: data?.latest_version?.params?.threat?.enabled,
			});
		} catch (error) {
			console.error("Error fetching classifier data", error);
		}
	}, [id, projectid]);

	useEffect(() => {
		if (id && projectid && !isModified && !isBasicModified) {
			fetchData();
		}

		// Warn user on exit without saving
		window.onbeforeunload = isModified || isBasicModified ? () => true : null;

		return () => {
			window.onbeforeunload = null;
		};
	}, [isModified, isBasicModified, id, projectid, fetchData]);

	const handleUpdateBasicInfo = async () => {
		try {
			await classifierService.updateClassifierBasicData(
				{
					project_id: projectid,
					classifier_id: id,
				},
				{
					name: classifierName,
					description: classifierDescription,
				}
			);
			setIsBasicModified(false);
			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.success"),
			});
		} catch (error) {
			console.error("Error applying classifier", error);
		}
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
			const res = await classifierService.updatePerspectiveApiClassifier(
				{
					project_id: projectid,
					classifier_id: id,
				},
				{
					classes: [],
					params,
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
			<ClassifierViewBreadcrumb
				record={classifier}
				projectid={projectid as string}
			/>
			<h1 className="flex items-center gap-2 text-2xl font-semibold">
				{translate("classifiers.types.perspective_api.edit_page.title")}
			</h1>
			<PerspectiveApiHeader />
			<Space h="md" />
			<div>
				<Divider
					my="sm"
					label={translate(
						"classifiers.types.manual_post_authors.view.accordion.basic_setup"
					)}
				/>
				<TextInput
					label={translate("projects.fields.name")}
					placeholder={translate("classifiers.fields.name_placeholder")}
					value={classifierName}
					onChange={(e) => {
						setIsBasicModified(true);
						setClassifierName(e.target.value);
					}}
					required
				/>
				<Space h="sm" />
				<TextInput
					label={translate("projects.fields.description")}
					placeholder={translate("classifiers.fields.description_placeholder")}
					value={classifierDescription}
					onChange={(e) => {
						setIsBasicModified(true);
						setClassifierDescription(e.target.value);
					}}
					required
				/>
				<Space h="sm" />
				<div className="flex justify-end">
					<Button
						leftIcon={<IconCheck size={16} />}
						mt="sm"
						onClick={handleUpdateBasicInfo}
					>
						{translate("buttons.update_basic_info")}
					</Button>
				</div>
			</div>
			<Space h="lg" />

			{/* Classes Section */}
			<Divider
				my="sm"
				label={translate(
					"classifiers.types.manual_post_authors.view.accordion.class_configuration"
				)}
			/>
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
					onClick={handleSave}
				>
					{translate("buttons.confirm_apply")}
				</Button>
			</div>
		</div>
	);
};

export default EditPerspectiveApiClassifier;
