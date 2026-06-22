"use client";

import React from "react";
import {
	Anchor,
	List,
	NumberInput,
	Select,
	Space,
	Text,
	TextInput,
	Tooltip,
} from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import { DatePicker } from "@mantine/dates";
import GatherInputs from "@components/inputs/gather-inputs";
import { TextField } from "@refinedev/mantine";
import { xAdvancedSearchBaseLink } from "src/utils/constants";

const today = new Date(new Date().setHours(0, 0, 0, 0));

export const initialFormValues: {
	name: string;
	limit_results_per_search: number;
	sort: string;
	search_list: string[];
	posts_created_after: Date | null;
	posts_created_before: Date | null;
} = {
	name: "",
	limit_results_per_search: 10,
	sort: "Latest",
	search_list: [],
	posts_created_after: null,
	posts_created_before: null,
};

const PHEONIX_MANUAL_LINK =
	"https://howtobuildup.notion.site/Gather-options-by-platform-c8d862cab6f94a3abc62874c4a5aee74#28e45657183e8076bb81e7be42326aa4";

const PHEONIX_MANUAL_LINK_GENERIC =
	"https://www.notion.so/howtobuildup/Gather-options-by-platform-c8d862cab6f94a3abc62874c4a5aee74#28045657183e80d3b5d2f4b5159982fe";

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.required"
				)
			: null;

	validationRules.sort =
		data.sort.length <= 0
			? translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.required"
				)
			: null;

	const search_list_length = data.search_list.length;

	if (search_list_length <= 0) {
		validationRules.search_list = translate(
			"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.required"
		);
	} else if (search_list_length > 200) {
		validationRules.search_list = translate(
			"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.search_list.too_many"
		);
	} else {
		validationRules.search_list = null;
	}

	validationRules.limit_results_per_search =
		data.limit_results_per_search === undefined
			? translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.required"
				)
			: null;
	validationRules.limit_results_per_search =
		data.limit_results_per_search > 50000
			? translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.limit_results_per_search_max"
				)
			: null;

	if (data.posts_created_after && data.posts_created_before) {
		const startDate = new Date(data.posts_created_after);
		const endDate = new Date(data.posts_created_before);

		if (startDate > today) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.posts_created_after.less_than_today"
			);
		}
		if (startDate > endDate) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.posts_created_after.less_than_end"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.posts_created_before.greater_than_start"
			);
		}
		// Calculate the difference (in days) between start and end
		const oneDayInMs = 1000 * 60 * 60 * 24;
		const diffInMs = endDate.getTime() - startDate.getTime();
		// Minus 1 as we want to exclude the end date
		const diffInDays = Math.floor(diffInMs / oneDayInMs) - 1;
		if (diffInDays > 365) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.posts_created_after.max_days"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_x_advanced_searches_posts_comments.fields.validation.posts_created_before.max_days"
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

const ApifyXAdvancedSearchesPostsCommentsForm: React.FC<Props> = ({
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
					"gathers.types.apify_x_advanced_searches_posts_comments.create_description.part1"
				)}
			/>
			<Space h="sm" />
			<Text>
				{translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.create_description.part2"
				)}
			</Text>
			<List>
				<List.Item>
					<Anchor
						className="font-normal hover:text-blue-500 text-sm underline"
						href={PHEONIX_MANUAL_LINK_GENERIC}
						target="_blank"
					>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.create_description.part3a"
						)}
					</Anchor>
				</List.Item>
				<List.Item>
					<Anchor
						className="font-normal hover:text-blue-500 text-sm underline"
						href={PHEONIX_MANUAL_LINK}
						target="_blank"
					>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.create_description.part3b"
						)}
					</Anchor>
				</List.Item>
			</List>
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
				max={50000}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.limit_results_per_search"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.limit_results_per_search"
						)}
					</div>
				}
				{...getInputProps("limit_results_per_search")}
			/>
			<DatePicker
				mt="lg"
				locale={currentLocale}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.posts_created_after"
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
								"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.posts_created_before"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.posts_created_before"
						)}
					</div>
				}
				{...getInputProps("posts_created_before")}
			/>
			<Select
				mt="lg"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.sort_by"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.sort_by"
						)}
					</div>
				}
				{...getInputProps("sort")}
				data={[
					{ label: translate("inputs.select"), value: "" },
					{
						label: translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.sort_by_options.top"
						),
						value: "Top",
					},
					{
						label: translate(
							"gathers.types.apify_x_advanced_searches_posts_comments.fields.sort_by_options.latest"
						),
						value: "Latest",
					},
				]}
			/>
			<TextField
				mt="xl"
				size={30}
				value={translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.search_queries"
				)}
			/>
			<Text fz="sm">
				{translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.search_queries.part1"
				)}
				<Anchor
					className="font-normal hover:text-blue-500 text-sm underline"
					href={PHEONIX_MANUAL_LINK}
					target="_blank"
				>
					{translate(
						"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.search_queries.part2"
					)}
				</Anchor>
				{translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.info.search_queries.part3"
				)}
			</Text>
			<GatherInputs
				placeholder={translate(
					"gathers.types.apify_x_advanced_searches_posts_comments.fields.search_queries_placeholder"
				)}
				data={inputList}
				setData={setInputList}
				split_regex={/[\n]+/}
				template_url_for_input={xAdvancedSearchBaseLink}
				{...getInputProps("search_list")}
			/>
		</>
	);
};

export default ApifyXAdvancedSearchesPostsCommentsForm;
