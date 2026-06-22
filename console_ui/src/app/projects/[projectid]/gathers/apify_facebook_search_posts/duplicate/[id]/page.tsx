"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyFacebookSearchPostsForm, {
	getPostValidationRules,
	getUpdatedFormValues,
	initialFormValues,
} from "@components/forms/gather/apify_facebook_search_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyFacebookSearchPostDuplicate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	const [inputList, setInputList] = useState<string[]>([]);
	const [proxyGroup, setProxyGroup] = useState("");
	const [proxyCountry, setProxyCountry] = useState<string | null>(null);
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
		setFieldValue("search_query", gatherData?.search_query);
		setFieldValue("limit_posts", gatherData?.limit_posts);
		setFieldValue("limit_retries", gatherData?.limit_retries);
		setFieldValue("recent_posts", gatherData?.recent_posts);
		if (gatherData?.proxy?.use_apify_proxy) {
			// Setting the value for "apify_proxy_country" with value from API call
			setProxyCountry(gatherData?.proxy?.apify_proxy_country);
			// Setting the value for "apify_proxy_country" with value from API call
			setProxyGroup(gatherData?.proxy?.apify_proxy_groups[0]);
		} else {
			setProxyGroup("no_proxy");
		}
	}, [gatherData, setProxyCountry, setProxyGroup, setFieldValue]);

	const handleSubmit = () => {
		const updatedFormValues = getUpdatedFormValues(
			formValues,
			proxyGroup,
			proxyCountry
		);
		handleGatherSave(
			`projects/${projectid}/gathers/apify_facebook_search_posts`,
			isValid,
			projectid as string,
			setLoading,
			mutate,
			translate,
			updatedFormValues,
			setInputList,
			reset,
			router,
			validate
		);
	};

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
				onClick: () => handleSubmit(),
			}}
		>
			<ApifyFacebookSearchPostsForm
				getInputProps={getInputProps}
				proxyCountry={proxyCountry}
				setProxyCountry={setProxyCountry}
			/>
		</Create>
	);
}
