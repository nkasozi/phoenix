"use client";

import { useParsed, useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyFacebookSearchPostsForm, {
	getPostValidationRules,
	getUpdatedFormValues,
	initialFormValues,
} from "@components/forms/gather/apify_facebook_search_posts_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyFacebookSearchPostEdit(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: editResourceLoading },
	} = useUpdate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid } = useParams();
	const { id } = useParsed();
	const [inputList, setInputList] = useState<string[]>([]);
	const [proxyGroup, setProxyGroup] = useState("");
	const [proxyCountry, setProxyCountry] = useState<string | null>(null);
	const [formResetAfterEditloading, setLoading] = useState<boolean>(false);

	const {
		getInputProps,
		saveButtonProps,
		values: formValues,
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
		if (gatherData?.proxy?.use_apify_proxy) {
			// Setting the value for "apify_proxy_country" with value from API call
			setProxyCountry(gatherData?.proxy?.apify_proxy_country);
			// Setting the value for "apify_proxy_country" with value from API call
			setProxyGroup(gatherData?.proxy?.apify_proxy_groups[0]);
		} else {
			setProxyGroup("no_proxy");
		}
	}, [gatherData, setProxyCountry, setProxyGroup]);

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
			validate,
			gatherData?.id as string
		);
	};

	return (
		<Edit
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.apify_facebook_search_posts.edit")}
				</Title>
			}
			isLoading={
				formLoading || editResourceLoading || formResetAfterEditloading
			}
			headerButtons={() => null}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () => handleSubmit(),
			}}
		>
			<ApifyFacebookSearchPostsForm
				proxyCountry={proxyCountry}
				setProxyCountry={setProxyCountry}
				getInputProps={getInputProps}
			/>
		</Edit>
	);
}
