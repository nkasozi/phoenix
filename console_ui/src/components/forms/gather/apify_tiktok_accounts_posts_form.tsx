"use client";

import React from "react";
import { NumberInput, Select, TextInput, Tooltip } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import { DatePicker } from "@mantine/dates";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";
import {
	tiktokCountryList,
	tiktokAccountSearchBaseLink,
} from "src/utils/constants";

interface FormValues {
	name: string;
	limit_posts_per_account: number;
	account_username_list: string[];
	posts_created_after: Date | null;
	posts_created_since_num_days: number | null;
	proxy_country_to_gather_from: string;
}

export const initialFormValues: FormValues = {
	name: "",
	limit_posts_per_account: 100,
	account_username_list: [],
	posts_created_after: null,
	posts_created_since_num_days: null,
	proxy_country_to_gather_from: "None",
};

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_tiktok_accounts_posts.fields.validation.required"
				)
			: null;
	validationRules.account_username_list =
		data.account_username_list.length <= 0
			? translate(
					"gathers.types.apify_tiktok_accounts_posts.fields.validation.required"
				)
			: null;
	validationRules.limit_posts_per_account =
		data.limit_posts_per_account === undefined
			? translate(
					"gathers.types.apify_tiktok_accounts_posts.fields.validation.required"
				)
			: null;
	validationRules.proxy_country_to_gather_from =
		!data.proxy_country_to_gather_from
			? translate(
					"gathers.types.apify_tiktok_accounts_posts.fields.validation.required"
				)
			: null;

	if (!data.posts_created_since_num_days && !data.posts_created_after) {
		validationRules.posts_created_after = translate(
			"gathers.types.apify_tiktok_accounts_posts.fields.validation.created_since_num_days_or_created_after"
		);
		validationRules.posts_created_since_num_days = translate(
			"gathers.types.apify_tiktok_accounts_posts.fields.validation.created_since_num_days_or_created_after"
		);
	}

	if (data.posts_created_since_num_days && data.posts_created_after) {
		validationRules.posts_created_after = translate(
			"gathers.types.apify_tiktok_accounts_posts.fields.validation.created_since_num_days_and_created_after"
		);
		validationRules.posts_created_since_num_days = translate(
			"gathers.types.apify_tiktok_accounts_posts.fields.validation.created_since_num_days_and_created_after"
		);
	}

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
}

const ApifyTiktokAccountsPostsForm: React.FC<Props> = ({
	getInputProps,
	inputList,
	setInputList,
}) => {
	const translate = useTranslate();
	return (
		<>
			<TextField
				value={translate(
					"gathers.types.apify_tiktok_accounts_posts.create_description"
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
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_tiktok_accounts_posts.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_tiktok_accounts_posts.fields.posts_created_after"
						)}
					</div>
				}
				disabled={getInputProps("posts_created_since_num_days").value}
				{...getInputProps("posts_created_after")}
			/>
			<NumberInput
				mt="lg"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_tiktok_accounts_posts.fields.info.posts_created_since_num_days"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_tiktok_accounts_posts.fields.posts_created_since_num_days"
						)}
					</div>
				}
				disabled={getInputProps("posts_created_after").value}
				{...getInputProps("posts_created_since_num_days")}
				onChange={(value) => {
					// Convert value to a number or null if empty
					const numericValue = value === undefined ? null : Number(value);
					// Trigger the onChange handler from getInputProps
					getInputProps("posts_created_since_num_days").onChange(numericValue);
				}}
			/>
			<NumberInput
				mt="lg"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_tiktok_accounts_posts.fields.info.limit_posts_per_account"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_tiktok_accounts_posts.fields.limit_posts_per_account"
						)}
					</div>
				}
				{...getInputProps("limit_posts_per_account")}
			/>
			<Select
				mt="lg"
				searchable
				clearable
				data={tiktokCountryList}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_tiktok_accounts_posts.fields.info.proxy_country_to_gather_from"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_tiktok_accounts_posts.fields.proxy_country_to_gather_from"
						)}
					</div>
				}
				{...getInputProps("proxy_country_to_gather_from")}
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
							"gathers.types.apify_tiktok_accounts_posts.fields.input.url_list"
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
				template_url_for_input={tiktokAccountSearchBaseLink}
				split_regex={/[,\n]+/}
				{...getInputProps("account_username_list")}
			/>
		</>
	);
};

export default ApifyTiktokAccountsPostsForm;
