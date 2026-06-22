"use client";

import React from "react";
import { useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import CreateEditProjectForm, {
	getProjectValidationRules,
	initialFormValues,
} from "@components/forms/create-edit-project";
import { useRouter } from "next/navigation";

export default function ProjectEdit(): JSX.Element {
	const translate = useTranslate();
	const { mutate } = useUpdate();
	const router = useRouter();
	const {
		getInputProps,
		saveButtonProps,
		values: formValues,
		isValid,
		validate,
		refineCore: { query: queryResult },
	} = useForm({
		initialValues: initialFormValues,
		validate: (values) => getProjectValidationRules(values, translate, "edit"),
	});

	const projectsData = queryResult?.data?.data;

	const handleSave = async () => {
		if (isValid()) {
			if (projectsData?.id) {
				mutate(
					{
						resource: "projects",
						id: projectsData.id,
						values: formValues,
						meta: {
							method: "put",
						},
					},
					{
						onSuccess: async () => {
							router.push(`/projects/show/${projectsData.id}`);
						},
					}
				);
			}
		} else {
			validate();
		}
	};

	return (
		<Edit
			saveButtonProps={{ ...saveButtonProps, onClick: handleSave }}
			canDelete={false}
		>
			<CreateEditProjectForm getInputProps={getInputProps} state="edit" />
		</Edit>
	);
}
