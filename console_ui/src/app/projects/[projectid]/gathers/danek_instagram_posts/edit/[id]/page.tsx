"use client";

import { useParsed, useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { handleGatherSave } from "src/utils/constants";
import DanekInstagramPostsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/danek_instagram_posts_form";

export default function DanekInstagramPostsEdit(): JSX.Element {
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
		validate: (values) => getPostValidationRules(values, translate),
	});

	const gatherData = queryResult?.data?.data;

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
		<Edit
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.danek_instagram_posts.edit")}
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
						validate,
						gatherData?.id as string
					),
			}}
		>
			<DanekInstagramPostsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Edit>
	);
}
