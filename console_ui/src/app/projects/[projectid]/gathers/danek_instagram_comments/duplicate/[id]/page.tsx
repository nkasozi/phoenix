"use client";

import { useCreate, useOne, useTranslate } from "@refinedev/core";
import { Create, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import DanekInstagramCommentsForm, {
	getCommentValidationRules,
	initialFormValues,
} from "@components/forms/gather/danek_instagram_comments_form";
import { handleGatherSave } from "src/utils/constants";

export default function DanekInstagramCommentsDuplicate(): JSX.Element {
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
		validate: (values) =>
			getCommentValidationRules(values, translate, inputList),
	});

	useEffect(() => {
		if (gatherData?.post_id_list) {
			setInputList(gatherData.post_id_list.map(String));
		}
		setFieldValue(
			"limit_comments_per_post",
			gatherData?.limit_comments_per_post
		);
		setFieldValue(
			"limit_child_comments_per_comment",
			gatherData?.limit_child_comments_per_comment
		);
	}, [gatherData, setFieldValue]);

	useEffect(() => {
		setFieldValue(
			"post_id_list",
			inputList
				.filter((value) => /^\d+$/.test(value.trim()))
				.map((value) => value.trim())
		);
	}, [inputList, setFieldValue]);

	return (
		<Create
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.danek_instagram_comments.create")}
				</Title>
			}
			isLoading={
				formLoading || createResourceLoading || formResetAfterCreateloading
			}
			saveButtonProps={{
				...saveButtonProps,
				onClick: () =>
					handleGatherSave(
						`projects/${projectid}/gathers/danek_instagram_comments`,
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
			<DanekInstagramCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Create>
	);
}
