"use client";

import React from "react";
import { NumberInput, TextInput, Tooltip } from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { DatePicker } from "@mantine/dates";
import { ProjectSchema } from "src/interfaces/project";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";
import { instagramAccountBaseLink } from "src/utils/constants";

interface FormValues {
	name: string;
	limit_posts_per_account: number;
	account_username_list: string[];
	posts_created_after: Date | null;
	scrape_comments_count_per_post: number;
	limit_child_comments_per_comment: number;
}

export const initialFormValues: FormValues = {
	name: "",
	limit_posts_per_account: 10,
	account_username_list: [],
	posts_created_after: null,
	scrape_comments_count_per_post: 0,
	limit_child_comments_per_comment: 0,
};

export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.danek_instagram_posts.fields.validation.required"
				)
			: null;
	validationRules.account_username_list =
		data.account_username_list.length <= 0
			? translate(
					"gathers.types.danek_instagram_posts.fields.validation.required"
				)
			: null;
	validationRules.limit_posts_per_account =
		data.limit_posts_per_account === undefined
			? translate(
					"gathers.types.danek_instagram_posts.fields.validation.required"
				)
			: null;
	validationRules.scrape_comments_count_per_post =
		data.scrape_comments_count_per_post === undefined
			? translate(
					"gathers.types.danek_instagram_posts.fields.validation.required"
				)
			: data.scrape_comments_count_per_post > 200
				? translate(
						"gathers.types.danek_instagram_posts.fields.validation.scrape_comments_count_per_post_max"
					)
				: null;
	validationRules.limit_child_comments_per_comment =
		data.limit_child_comments_per_comment === undefined
			? translate(
					"gathers.types.danek_instagram_posts.fields.validation.required"
				)
			: null;

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
}

const DanekInstagramPostsForm: React.FC<Props> = ({
	getInputProps,
	inputList,
	setInputList,
}) => {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();

	return (
		<>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_instagram_posts.create_description.part1"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_instagram_posts.create_description.part2"
				)}
			/>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.danek_instagram_posts.create_description.part3"
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
								"gathers.types.danek_instagram_posts.fields.info.limit_posts_per_account"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_posts.fields.limit_posts_per_account"
						)}
					</div>
				}
				{...getInputProps("limit_posts_per_account")}
			/>
			<DatePicker
				mt="lg"
				clearable
				locale={currentLocale}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_instagram_posts.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_posts.fields.posts_created_after"
						)}
					</div>
				}
				{...getInputProps("posts_created_after")}
			/>
			<NumberInput
				mt="lg"
				min={0}
				max={200}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_instagram_posts.fields.info.scrape_comments_count_per_post"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_posts.fields.scrape_comments_count_per_post"
						)}
					</div>
				}
				{...getInputProps("scrape_comments_count_per_post")}
			/>
			<NumberInput
				mt="lg"
				min={0}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_instagram_posts.fields.info.limit_child_comments_per_comment"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_instagram_posts.fields.limit_child_comments_per_comment"
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
							"gathers.types.danek_instagram_posts.fields.input.url_list"
						)}
						{inputList.length > 0 && (
							<span className="italic ml-10">
								{inputList.length}{" "}
								{translate("gathers.fields.source.input_values")}
							</span>
						)}
					</div>
				}
				placeholder={translate("gathers.fields.input.data_placeholder")}
				data={inputList}
				setData={setInputList}
				template_url_for_input={instagramAccountBaseLink}
				split_regex={/[,\n]+/}
				{...getInputProps("account_username_list")}
			/>
		</>
	);
};

export default DanekInstagramPostsForm;
