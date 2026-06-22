"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import DanekFacebookSearchesPostsForm, {
	getPostValidationRules,
	initialFormValues,
} from "@components/forms/gather/danek_facebook_searches_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function DanekFacebookSearchesPostDuplicate(): JSX.Element {
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
		setFieldValue("recent_posts", gatherData?.recent_posts);
		// Updating the "search_list" with values from local state
		if (gatherData?.search_list) {
			setInputList(gatherData.search_list);
		}
		// Setting the value for "stop_scraping_per_search_after_count" with value from API call
		setFieldValue(
			"stop_scraping_per_search_after_count",
			gatherData?.stop_scraping_per_search_after_count
		);
		// Setting the value for "proxy_country_to_gather_from" with value from API call
		setFieldValue(
			"proxy_country_to_gather_from",
			gatherData?.proxy_country_to_gather_from
		);
		// Setting the value for "posts_created_before" with value from API call
		setFieldValue(
			"posts_created_before",
			new Date(gatherData?.posts_created_before)
		);
		// Setting the value for "posts_created_after" with value from API call
		setFieldValue(
			"posts_created_after",
			new Date(gatherData?.posts_created_after)
		);
	}, [gatherData, setFieldValue]);

	useEffect(() => {
		setFieldValue("search_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.danek_facebook_searches_posts.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/danek_facebook_searches_posts`,
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
			<DanekFacebookSearchesPostsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
