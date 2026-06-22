"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyFacebookPostsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_facebook_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyFacebookPostDuplicate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	const [inputList, setInputList] = useState<string[]>([]);
	const [formResetAfterCreateloading, setLoading] = useState<boolean>(false);
	const { result: projectsData } = useOne({
		resource: `projects/${projectid}/gathers`,
		id: id as string,
	});

	const {
		getInputProps,
		saveButtonProps,
		values: formValues,
		setFieldValue,
		isValid,
		validate,
		reset,
		refineCore: { formLoading },
	} = useForm({
		clearInputErrorOnChange: true,
		initialValues: initialFormValues,
		validate: (values) => getPostValidationRules(values, translate),
	});

	useEffect(() => {
		// Updating the "account_url_list" with values from local state
		if (projectsData?.account_url_list) {
			setInputList(projectsData.account_url_list);
		}
		// Setting the value for "limit_posts_per_account" with value from API call
		setFieldValue(
			"limit_posts_per_account",
			projectsData?.limit_posts_per_account
		);
		// Setting the value for "posts_created_before" with value from API call
		setFieldValue(
			"posts_created_before",
			new Date(projectsData?.posts_created_before)
		);
		// Setting the value for "posts_created_after" with value from API call
		setFieldValue(
			"posts_created_after",
			new Date(projectsData?.posts_created_after)
		);
	}, [projectsData, setFieldValue]);

	useEffect(() => {
		setFieldValue("account_url_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.apify_facebook_posts.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/apify_facebook_posts`,
						isValid,
						projectid as string,
						setLoading,
						mutate,
						translate,
						formValues,
						setInputList,
						reset,
						router,
						validate
					),
			}}
		>
			<ApifyFacebookPostsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
