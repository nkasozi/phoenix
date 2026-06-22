"use client";

import React from "react";
import { Checkbox, NumberInput, TextInput, Tooltip } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";

const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

export const initialFormValues = {
	name: "",
	limit_total_comments: 1000,
	include_comment_replies: false,
	post_url_list: [] as string[],
};

// Define separate validation rules for comments
export function getCommentValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_tiktok_comments.fields.validation.required"
				)
			: null;
	validationRules.post_url_list =
		data.post_url_list.length <= 0
			? translate(
					"gathers.types.apify_tiktok_comments.fields.validation.required"
				)
			: null;
	validationRules.limit_total_comments =
		data.limit_total_comments === undefined
			? translate(
					"gathers.types.apify_facebook_comments.fields.validation.required"
				)
			: null;

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
}

const ApifyTiktokommentsForm: React.FC<Props> = ({
	getInputProps,
	inputList,
	setInputList,
}) => {
	const translate = useTranslate();
	return (
		<>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.apify_tiktok_comments.create_description.part1"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.apify_tiktok_comments.create_description.part2.main"
				)}
			/>
			<TextField
				value={translate(
					"gathers.types.apify_tiktok_comments.create_description.part2.a"
				)}
			/>
			<TextField
				value={translate(
					"gathers.types.apify_tiktok_comments.create_description.part2.b"
				)}
			/>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.apify_tiktok_comments.create_description.part2.c"
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
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_tiktok_comments.fields.info.limit_total_comments"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_tiktok_comments.fields.limit_total_comments"
						)}
					</div>
				}
				{...getInputProps("limit_total_comments")}
			/>
			<Checkbox
				mt="lg"
				label={translate(
					"gathers.types.apify_tiktok_comments.fields.include_comment_replies"
				)}
				{...getInputProps("include_comment_replies", { type: "checkbox" })}
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
							"gathers.types.apify_tiktok_comments.fields.input.url_list"
						)}
						{inputList.length > 0 && (
							<span className="italic ml-10">
								{inputList.length} input value{inputList.length > 1 && "s"}
							</span>
						)}
					</div>
				}
				placeholder={translate("gathers.fields.input.data_placeholder")}
				data={inputList}
				setData={setInputList}
				split_regex={/[,\n]+/}
				{...getInputProps("post_url_list")}
			/>
		</>
	);
};

export default ApifyTiktokommentsForm;
