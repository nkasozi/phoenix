"use client";

import { useCreate, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useState } from "react";
import ManualUploadForm, {
	getManualUploadValidationRules,
	initialFormValues,
} from "@components/forms/gather/manual_upload_form";
import ManualUploadGatherChecks from "@components/gather/manual_upload";

export default function ManualUploadGatherCreate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid } = useParams();
	const [file, setFile] = useState<File | null>(null);
	const [formResetAfterCreateloading, setLoading] = useState<boolean>(false);
	const [responseError, setResponseError] = useState({});

	const {
		getInputProps,
		saveButtonProps,
		values: formValues,
		isValid,
		validate,
		refineCore: { formLoading },
	} = useForm({
		clearInputErrorOnChange: true,
		initialValues: initialFormValues,
		validate: (values) => getManualUploadValidationRules(values, translate),
	});

	const prepareFormData = () => {
		const formData = new FormData();

		// Append form values to FormData
		Object.entries(formValues).forEach(([key, value]: any) => {
			if (key !== "file") {
				formData.append(key, value);
			}
		});

		// Append the file to FormData if it exists
		if (file) {
			formData.append("file", file);
		}

		return formData;
	};

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.manual_upload.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () => {
					setResponseError("");
					if (isValid()) {
						if (projectid) {
							setLoading(true);
							const formData = prepareFormData();
							mutate(
								{
									resource: `projects/${projectid}/gathers/manual_upload/`,
									values: formData,
									errorNotification: (res: any) => {
										let message = translate("gathers.errors.create");
										if (!res.response) {
											setResponseError({
												detail: {
													error_message: message,
												},
											});
										} else {
											setResponseError(res.response.data);
										}
										if (res?.response?.data?.detail[0]?.msg) {
											message = res.response.data.detail[0].msg;
										}
										return {
											message,
											description: "Error",
											type: "error",
										};
									},
								},
								{
									onSuccess: async () => {
										setTimeout(() => {
											router.push(
												`/projects/show/${projectid}?activeItem=gather`
											);
										}, 1000);
									},
									onError: () => {
										setLoading(false);
									},
								}
							);
						}
					} else {
						validate();
					}
				},
			}}
		>
			<ManualUploadForm
				getInputProps={getInputProps}
				file={file}
				setFile={setFile}
			/>
			<ManualUploadGatherChecks response={responseError} />
		</Create>
	);
}
