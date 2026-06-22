"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import DanekInstagramPostsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/danek_instagram_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function DanekInstagramPostsDuplicate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	const [inputList, setInputList] = useState<string[]>([]);
	const [formResetAfterCreateloading, setLoading] = useState<boolean>(false);
	const { result: gatherData } = useOne({
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
		if (gatherData?.account_username_list) {
			setInputList(gatherData.account_username_list);
		}
		setFieldValue(
			"limit_posts_per_account",
			gatherData?.limit_posts_per_account
		);
		setFieldValue(
			"scrape_comments_count_per_post",
			gatherData?.scrape_comments_count_per_post
		);
		setFieldValue(
			"limit_child_comments_per_comment",
			gatherData?.limit_child_comments_per_comment
		);
		setFieldValue(
			"posts_created_after",
			gatherData?.posts_created_after
				? new Date(gatherData.posts_created_after)
				: null
		);
	}, [gatherData, setFieldValue]);

	useEffect(() => {
		setFieldValue("account_username_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.danek_instagram_posts.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/danek_instagram_posts`,
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
			<DanekInstagramPostsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
