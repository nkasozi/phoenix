"use client";

import { useParsed, useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { handleGatherSave } from "src/utils/constants";
import ApifyXSimpleSearchesPostsCommentsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_x_simple_searches_posts_comments_form";

export default function ApifyXSimpleSearchesEdit(): JSX.Element {
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
	const [handleList, setHandleList] = useState<string[]>([]);
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

	const projectsData = queryResult?.data?.data;

	useEffect(() => {
		// Updating the "keywords_list" with values from local state
		if (projectsData?.keywords_list) {
			setInputList(projectsData.keywords_list);
		}
		// Updating the "handle_list" with values from local state
		if (projectsData?.handle_list) {
			setHandleList(projectsData.handle_list);
		}
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
		<Edit
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate(
						"gathers.types.apify_x_simple_searches_posts_comments.edit"
					)}
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
						validate,
						projectsData?.id as string
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
		</Edit>
	);
}
