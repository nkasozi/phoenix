"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyXSimpleSearchesPostsCommentsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_x_simple_searches_posts_comments_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyXSimpleSearchesDuplicate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	const [inputList, setInputList] = useState<string[]>([]);
	const [handleList, setHandleList] = useState<string[]>([]);
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
		// Updating the "keywords_list" with values from local state
		if (projectsData?.keywords_list) {
			setInputList(projectsData.keywords_list);
		}
		// Updating the "handle_list" with values from local state
		if (projectsData?.handle_list) {
			setHandleList(projectsData.handle_list);
		}
		// Setting the value for "sort" with value from API call
		setFieldValue("sort", projectsData?.sort);
		// Setting the value for "location" with value from API call
		setFieldValue("location_near", projectsData?.location_near);
		// Setting the value for "limit_results_per_search" with value from API call
		setFieldValue(
			"limit_results_per_search",
			projectsData?.limit_results_per_search
		);
		// Setting the value for "posts_created_before" with value from API call
		if (projectsData?.posts_created_before) {
			setFieldValue(
				"posts_created_before",
				new Date(projectsData?.posts_created_before)
			);
		}
		// Setting the value for "posts_created_after" with value from API call
		if (projectsData?.posts_created_after) {
			setFieldValue(
				"posts_created_after",
				new Date(projectsData?.posts_created_after)
			);
		}
	}, [projectsData, setFieldValue]);

	useEffect(() => {
		// Updating the "handle_list" with values from local state
		setFieldValue("handle_list", handleList);
	}, [handleList, setFieldValue]);

	useEffect(() => {
		// Updating the "keywords_list" with values from local state
		setFieldValue("keywords_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate(
						"gathers.types.apify_x_simple_searches_posts_comments.create"
					)}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/apify_x_simple_searches_posts_comments`,
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
			<ApifyXSimpleSearchesPostsCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
				handleList={handleList}
				setHandleList={setHandleList}
			/>
		</Create>
	);
}
