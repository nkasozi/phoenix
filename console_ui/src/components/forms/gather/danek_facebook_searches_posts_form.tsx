"use client";

import React from "react";
import {
	Checkbox,
	NumberInput,
	Select,
	TextInput,
	Tooltip,
} from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { DatePicker } from "@mantine/dates";
import { ProjectSchema } from "src/interfaces/project";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";
import {
	danekCountryList,
	facebookSearchPostBaseLink,
} from "src/utils/constants";

const today = new Date(new Date().setHours(0, 0, 0, 0));
const tomorrow = new Date(new Date().setHours(0, 0, 0, 0));
tomorrow.setDate(tomorrow.getDate() + 1);

interface FormValues {
	name: string;
	stop_scraping_per_search_after_count: number;
	posts_created_after: Date;
	posts_created_before: Date;
	proxy_country_to_gather_from: string | null;
	search_list: string[];
	recent_posts: boolean;
}

export const initialFormValues: FormValues = {
	name: "",
	stop_scraping_per_search_after_count: 100,
	proxy_country_to_gather_from: null,
	posts_created_after: today,
	posts_created_before: tomorrow,
	search_list: [],
	recent_posts: true,
};

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.danek_facebook_searches_posts.fields.validation.required"
				)
			: null;
	validationRules.search_list =
		data.search_list.length <= 0
			? translate(
					"gathers.types.danek_facebook_searches_posts.fields.validation.required"
				)
			: null;
	validationRules.stop_scraping_per_search_after_count =
		data.stop_scraping_per_search_after_count === undefined
			? translate(
					"gathers.types.danek_facebook_searches_posts.fields.validation.required"
				)
			: null;
	validationRules.posts_created_after = !data.posts_created_after
		? translate(
				"gathers.types.danek_facebook_searches_posts.fields.validation.required"
			)
		: null;
	validationRules.posts_created_before = !data.posts_created_before
		? translate(
				"gathers.types.danek_facebook_searches_posts.fields.validation.required"
			)
		: null;

	if (data.posts_created_after && data.posts_created_before) {
		const startDate = new Date(data.posts_created_after);
		const endDate = new Date(data.posts_created_before);

		if (startDate > today) {
			validationRules.posts_created_after = translate(
				"gathers.types.danek_facebook_searches_posts.fields.validation.posts_created_after.less_than_today"
			);
		}
		if (startDate > endDate) {
			validationRules.posts_created_after = translate(
				"gathers.types.danek_facebook_searches_posts.fields.validation.posts_created_after.less_than_end"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.danek_facebook_searches_posts.fields.validation.posts_created_before.greater_than_start"
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

const DanekFacebookSearchesPostsForm: React.FC<Props> = ({
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
					"gathers.types.danek_facebook_searches_posts.create_description.part1"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_facebook_searches_posts.create_description.part2"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.danek_facebook_searches_posts.create_description.part3"
				)}
			/>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.danek_facebook_searches_posts.create_description.part4"
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
								"gathers.types.danek_facebook_searches_posts.fields.info.stop_scraping_per_search_after_count"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_facebook_searches_posts.fields.stop_scraping_per_search_after_count"
						)}
					</div>
				}
				{...getInputProps("stop_scraping_per_search_after_count")}
			/>
			<DatePicker
				mt="lg"
				locale={currentLocale}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_facebook_searches_posts.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_facebook_searches_posts.fields.posts_created_after"
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
								"gathers.types.danek_facebook_searches_posts.fields.info.posts_created_before"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_facebook_searches_posts.fields.posts_created_before"
						)}
					</div>
				}
				{...getInputProps("posts_created_before")}
			/>
			<Checkbox
				mt="lg"
				label={
					<div className="flex items-center">
						{translate(
							"gathers.types.danek_facebook_searches_posts.fields.recent_posts"
						)}
						<Tooltip
							width={350}
							multiline
							label={translate(
								"gathers.types.danek_facebook_searches_posts.fields.info.recent_posts"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
					</div>
				}
				{...getInputProps("recent_posts", { type: "checkbox" })}
			/>
			<Select
				mt="lg"
				searchable
				clearable
				data={danekCountryList}
				placeholder={translate("gathers.fields.input.select_placeholder")}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.danek_facebook_searches_posts.fields.info.proxy_country_to_gather_from"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.danek_facebook_searches_posts.fields.proxy_country_to_gather_from"
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
							"gathers.types.danek_facebook_searches_posts.fields.input.url_list"
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
				template_url_for_input={facebookSearchPostBaseLink}
				split_regex={/[,\n]+/}
				{...getInputProps("search_list")}
			/>
		</>
	);
};

export default DanekFacebookSearchesPostsForm;
