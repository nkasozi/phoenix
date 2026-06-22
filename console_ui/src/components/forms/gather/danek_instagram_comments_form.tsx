"use client";

import React from "react";
import { NumberInput, TextInput, Tooltip } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";

interface FormValues {
	name: string;
	post_id_list: string[];
	limit_comments_per_post: number;
	limit_child_comments_per_comment: number;
}

export const initialFormValues: FormValues = {
	name: "",
	post_id_list: [],
	limit_comments_per_post: 50,
	limit_child_comments_per_comment: 0,
};

export function getCommentValidationRules(
	data: any,
	translate: any,
	inputList: string[]
) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.danek_instagram_comments.fields.validation.required"
				)
			: null;
	validationRules.post_id_list =
		inputList.length <= 0
			? translate(
					"gathers.types.danek_instagram_comments.fields.validation.required"
				)
			: inputList.some((value) => !/^\d+$/.test(value.trim()))
				? translate(
						"gathers.types.danek_instagram_comments.fields.validation.numeric_post_ids"
					)
				: null;
	validationRules.limit_comments_per_post =
		data.limit_comments_per_post === undefined
			? translate(
					"gathers.types.danek_instagram_comments.fields.validation.required"
				)
			: null;
	validationRules.limit_child_comments_per_comment =
		data.limit_child_comments_per_comment === undefined
			? translate(
					"gathers.types.danek_instagram_comments.fields.validation.required"
				)
			: null;

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
}

const DanekInstagramCommentsForm: React.FC<Props> = ({
	getInputProps,
	inputList,
	setInputList,
}) => {
	const translate = useTranslate();

	return (
		<>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_instagram_comments.create_description.part1"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_instagram_comments.create_description.part2"
				)}
			/>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.danek_instagram_comments.create_description.part3"
				)}
			/>
			<TextInput
				mt="sm"
				label={
					<div className="flex items-center">
						<Tooltip label={translate("gathers.fields.info.name")}>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("gathers.fields.input.name")}
					</div>
				}
				{...getInputProps("name")}
			/>
			<NumberInput
				mt="lg"
				min={0}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_instagram_comments.fields.info.limit_comments_per_post"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_comments.fields.limit_comments_per_post"
						)}
					</div>
				}
				{...getInputProps("limit_comments_per_post")}
			/>
			<NumberInput
				mt="lg"
				min={0}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_instagram_comments.fields.info.limit_child_comments_per_comment"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_comments.fields.limit_child_comments_per_comment"
						)}
					</div>
				}
				{...getInputProps("limit_child_comments_per_comment")}
			/>
			<GatherInputs
				label={
					<div className="flex items-center">
						<Tooltip label={translate("gathers.fields.input.data_placeholder")}>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_comments.fields.input.url_list"
						)}
						{inputList.length > 0 && (
							<span className="italic ml-10">
								{inputList.length}{" "}
								{translate("gathers.fields.source.input_values")}
							</span>
						)}
					</div>
				}
				placeholder={translate(
					"gathers.types.danek_instagram_comments.fields.input.data_placeholder"
				)}
				data={inputList}
				setData={setInputList}
				link={false}
				split_regex={/[,\n]+/}
				{...getInputProps("post_id_list")}
			/>
		</>
	);
};

export default DanekInstagramCommentsForm;
