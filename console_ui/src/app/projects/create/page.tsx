"use client";

import CreateEditProjectForm, {
	getProjectValidationRules,
	initialFormValues,
} from "@components/forms/create-edit-project";
import { useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import React from "react";

export default function ProjectCreate(): JSX.Element {
	const translate = useTranslate();
	const {
		getInputProps,
		saveButtonProps,
		refineCore: { formLoading },
	} = useForm({
		initialValues: initialFormValues,
		validate: (values) => getProjectValidationRules(values, translate),
	});

	return (
		<Create isLoading={formLoading} saveButtonProps={saveButtonProps}>
			<CreateEditProjectForm getInputProps={getInputProps} />
		</Create>
	);
}
