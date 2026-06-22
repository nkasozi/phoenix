"use client";

import { useParsed, useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyTiktokCommentsForm, {
	getCommentValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_tiktok_comments_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyFacebookPostEdit(): JSX.Element {
	const today = new Date();
	const tomorrow = new Date(today);
	tomorrow.setDate(tomorrow.getDate() + 1);
	const {
		mutate,
		mutation: { isPending: editResourceLoading },
	} = useUpdate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid } = useParams();
	const { id } = useParsed();
	const [inputList, setInputList] = useState<string[]>([]);
	const [formResetAfterEditloading, setLoading] = useState<boolean>(false);

	const {
		getInputProps,
		saveButtonProps,
		values: formValues,
		setFieldValue,
		isValid,
		validate,
		reset,
		refineCore: { formLoading, query: queryResult },
	} = useForm({
		refineCoreProps: {
			resource: `projects/${projectid}/gathers`,
			action: "edit",
			id,
		},
		clearInputErrorOnChange: true,
		initialValues: initialFormValues,
		validate: (values) => getCommentValidationRules(values, translate),
	});

	const projectsData = queryResult?.data?.data;

	useEffect(() => {
		// Updating the "post_url_list" with values from local state
		if (projectsData?.post_url_list) {
			setInputList(projectsData.post_url_list);
		}
	}, [projectsData, setFieldValue]);

	useEffect(() => {
		setFieldValue("post_url_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Edit
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.apify_tiktok_comments.edit")}
				</Title>
			}
			isLoading={
				formLoading || editResourceLoading || formResetAfterEditloading
			}
			headerButtons={() => null}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/apify_tiktok_comments`,
						isValid,
						projectid as string,
						setLoading,
						mutate,
						translate,
						formValues,
						setInputList,
						reset,
						router,
						validate,
						projectsData?.id as string
					),
			}}
		>
			<ApifyTiktokCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Edit>
	);
}
