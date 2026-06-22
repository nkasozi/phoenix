"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyXAdvancedSearchesPostsCommentsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_x_advanced_searches_posts_comments_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyXAdvancedSearchesDuplicate(): JSX.Element {
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
		// Updating the "search_list" with values from local state
		if (projectsData?.search_list) {
			setInputList(projectsData.search_list);
		}
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
		setFieldValue("sort", projectsData?.sort);
	}, [projectsData, setFieldValue]);

	useEffect(() => {
		setFieldValue("search_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate(
						"gathers.types.apify_x_advanced_searches_posts_comments.create"
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
						`projects/${projectid}/gathers/apify_x_advanced_searches_posts_comments`,
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
			<ApifyXAdvancedSearchesPostsCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
