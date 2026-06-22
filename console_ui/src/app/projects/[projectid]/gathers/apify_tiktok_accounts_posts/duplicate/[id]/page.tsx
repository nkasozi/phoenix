"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyTiktokAccountsPostsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_tiktok_accounts_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyTiktokAccountsPostDuplicate(): JSX.Element {
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
		// Updating the "account_username_list" with values from local state
		if (projectsData?.account_username_list) {
			setInputList(projectsData.account_username_list);
		}
		// Setting the value for "limit_posts_per_account" with value from API call
		setFieldValue(
			"limit_posts_per_account",
			projectsData?.limit_posts_per_account
		);
		// Setting the value for "posts_created_since_num_days" with value from API call
		setFieldValue(
			"posts_created_since_num_days",
			projectsData?.posts_created_since_num_days
		);
		// Setting the value for "proxy_country_to_gather_from" with value from API call
		setFieldValue(
			"proxy_country_to_gather_from",
			projectsData?.proxy_country_to_gather_from
		);
		// Setting the value for "posts_created_after" with value from API call
		setFieldValue(
			"posts_created_after",
			projectsData?.posts_created_after
				? new Date(projectsData.posts_created_after)
				: null
		);
	}, [projectsData, setFieldValue]);

	useEffect(() => {
		setFieldValue("account_username_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.apify_tiktok_accounts_posts.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/apify_tiktok_accounts_posts`,
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
			<ApifyTiktokAccountsPostsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
