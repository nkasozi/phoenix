"use client";

import { useCreate, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import ApifyTiktokCommentsForm, {
	getCommentValidationRules,
	initialFormValues,
} from "@components/forms/gather/apify_tiktok_comments_form";
import { handleGatherSave } from "src/utils/constants";

export default function ApifyTiktokCommentCreate(): JSX.Element {
	const {
		mutate,
		mutation: { isPending: createResourceLoading },
	} = useCreate();
	const translate = useTranslate();
	const router = useRouter();
	const { projectid } = useParams();
	const [inputList, setInputList] = useState<string[]>([]);
	const [formResetAfterCreateloading, setLoading] = useState<boolean>(false);

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
		validate: (values) => getCommentValidationRules(values, translate),
	});

	useEffect(() => {
		// Updating the "post_url_list" with values from local state
		setFieldValue("post_url_list", inputList);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.apify_tiktok_comments.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/apify_tiktok_comments`,
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
			<ApifyTiktokCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
