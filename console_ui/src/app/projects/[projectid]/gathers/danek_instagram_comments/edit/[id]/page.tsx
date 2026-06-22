"use client";

import { useParsed, useTranslate, useUpdate } from "@refinedev/core";
import { Edit, useForm } from "@refinedev/mantine";
import { Title } from "@mantine/core";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { handleGatherSave } from "src/utils/constants";
import DanekInstagramCommentsForm, {
	getCommentValidationRules,
	initialFormValues,
} from "@components/forms/gather/danek_instagram_comments_form";

export default function DanekInstagramCommentsEdit(): JSX.Element {
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
		validate: (values) =>
			getCommentValidationRules(values, translate, inputList),
	});

	const gatherData = queryResult?.data?.data;

	useEffect(() => {
		if (gatherData?.post_id_list) {
			setInputList(gatherData.post_id_list.map(String));
		}
	}, [gatherData]);

	useEffect(() => {
		setFieldValue(
			"post_id_list",
			inputList
				.filter((value) => /^\d+$/.test(value.trim()))
				.map((value) => value.trim())
		);
	}, [inputList, setFieldValue]);

	return (
		<Edit
			breadcrumb={null}
			title={
				<Title order={3}>
					{translate("gathers.types.danek_instagram_comments.edit")}
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
						validate,
						gatherData?.id as string
					),
			}}
		>
			<DanekInstagramCommentsForm
				getInputProps={getInputProps}
				inputList={inputList}
				setInputList={setInputList}
			/>
		</Edit>
	);
}
