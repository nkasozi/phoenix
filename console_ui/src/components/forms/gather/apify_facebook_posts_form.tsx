"use client";

import React from "react";
import { NumberInput, TextInput, Tooltip } from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import { DatePicker } from "@mantine/dates";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";

const today = new Date(new Date().setHours(0, 0, 0, 0));
const tomorrow = new Date(new Date().setHours(0, 0, 0, 0));
tomorrow.setDate(tomorrow.getDate() + 1);

export const initialFormValues = {
	name: "",
	limit_posts_per_account: 1000,
	account_url_list: [] as string[],
	posts_created_after: today,
	posts_created_before: tomorrow,
};

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_facebook_posts.fields.validation.required"
				)
			: null;

	const account_url_list_length = data.account_url_list.length;

	if (account_url_list_length <= 0) {
		validationRules.account_url_list = translate(
			"gathers.types.apify_facebook_posts.fields.validation.required"
		);
	} else if (account_url_list_length > 200) {
		validationRules.account_url_list = translate(
			"gathers.types.apify_facebook_posts.fields.validation.account_url_list.too_many"
		);
	} else {
		validationRules.account_url_list = null;
	}

	validationRules.limit_posts_per_account =
		data.limit_posts_per_account === undefined
			? translate(
					"gathers.types.apify_facebook_posts.fields.validation.required"
				)
			: null;
	validationRules.limit_posts_per_account =
		data.limit_posts_per_account > 50000
			? translate(
					"gathers.types.apify_facebook_posts.fields.validation.limit_posts_per_account_max"
				)
			: null;
	validationRules.posts_created_after = !data.posts_created_after
		? translate("gathers.types.apify_facebook_posts.fields.validation.required")
		: null;
	validationRules.posts_created_before = !data.posts_created_before
		? translate("gathers.types.apify_facebook_posts.fields.validation.required")
		: null;

	if (data.posts_created_after && data.posts_created_before) {
		const startDate = new Date(data.posts_created_after);
		const endDate = new Date(data.posts_created_before);

		if (startDate > today) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_facebook_posts.fields.validation.posts_created_after.less_than_today"
			);
		}
		if (startDate > endDate) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_facebook_posts.fields.validation.posts_created_after.less_than_end"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_facebook_posts.fields.validation.posts_created_before.greater_than_start"
			);
		}
		// Calculate the difference (in days) between start and end
		const oneDayInMs = 1000 * 60 * 60 * 24;
		const diffInMs = endDate.getTime() - startDate.getTime();
		// Minus 1 as we want to exclude the end date
		const diffInDays = Math.floor(diffInMs / oneDayInMs) - 1;
		if (diffInDays > 365) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_facebook_posts.fields.validation.posts_created_after.max_days"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_facebook_posts.fields.validation.posts_created_before.max_days"
			);
		}
	}

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
}

const ApifyFacebookPostsForm: React.FC<Props> = ({
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
				value={translate(
					"gathers.types.apify_facebook_posts.create_description"
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
			<DatePicker
				mt="lg"
				locale={currentLocale}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_posts.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_posts.fields.posts_created_after"
						)}
					</div>
				}
				{...getInputProps("posts_created_after")}
			/>
			<DatePicker
				mt="lg"
				locale={currentLocale}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_posts.fields.info.posts_created_before"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_posts.fields.posts_created_before"
						)}
					</div>
				}
				{...getInputProps("posts_created_before")}
			/>
			<NumberInput
				mt="lg"
				max={50000}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_posts.fields.info.limit_posts_per_account"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_posts.fields.limit_posts_per_account"
						)}
					</div>
				}
				{...getInputProps("limit_posts_per_account")}
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
							"gathers.types.apify_facebook_posts.fields.input.url_list"
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
				{...getInputProps("account_url_list")}
			/>
		</>
	);
};

export default ApifyFacebookPostsForm;
