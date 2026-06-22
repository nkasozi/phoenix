"use client";

import React from "react";
import {
	Anchor,
	Group,
	Indicator,
	List,
	NumberInput,
	Select,
	Space,
	Tabs,
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

const today = new Date(new Date().setHours(0, 0, 0, 0));

export const initialFormValues: {
	name: string;
	limit_results_per_search: number;
	keywords_list: string[];
	handle_list: string[];
	sort: string;
	location_near: string;
	posts_created_after: Date | null;
	posts_created_before: Date | null;
} = {
	name: "",
	limit_results_per_search: 10,
	keywords_list: [],
	handle_list: [],
	sort: "Latest",
	location_near: "",
	posts_created_after: null,
	posts_created_before: null,
};

const PHEONIX_MANUAL_LINK =
	"https://www.notion.so/howtobuildup/Gather-options-by-platform-c8d862cab6f94a3abc62874c4a5aee74#28e45657183e80928fceda0bcaeb38c0";

const PHEONIX_MANUAL_LINK_GENERIC =
	"https://www.notion.so/howtobuildup/Gather-options-by-platform-c8d862cab6f94a3abc62874c4a5aee74#28045657183e80d3b5d2f4b5159982fe";

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.required"
				)
			: null;

	validationRules.sort =
		data.sort.length <= 0
			? translate(
					"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.required"
				)
			: null;

	validationRules.limit_results_per_search =
		data.limit_results_per_search === undefined
			? translate(
					"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.required"
				)
			: null;
	validationRules.limit_results_per_search =
		data.limit_results_per_search > 50000
			? translate(
					"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.limit_results_per_search_max"
				)
			: null;

	if (data.posts_created_after && data.posts_created_before) {
		const startDate = new Date(data.posts_created_after);
		const endDate = new Date(data.posts_created_before);

		if (startDate > today) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.posts_created_after.less_than_today"
			);
		}
		if (startDate > endDate) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.posts_created_after.less_than_end"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.posts_created_before.greater_than_start"
			);
		}
		// Calculate the difference (in days) between start and end
		const oneDayInMs = 1000 * 60 * 60 * 24;
		const diffInMs = endDate.getTime() - startDate.getTime();
		// Minus 1 as we want to exclude the end date
		const diffInDays = Math.floor(diffInMs / oneDayInMs) - 1;
		if (diffInDays > 365) {
			validationRules.posts_created_after = translate(
				"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.posts_created_after.max_days"
			);
			validationRules.posts_created_before = translate(
				"gathers.types.apify_x_simple_searches_posts_comments.fields.validation.posts_created_before.max_days"
			);
		}
	}

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	inputList: string[];
	setInputList: any;
	handleList: string[];
	setHandleList: any;
}

const ApifyXSimpleSearchesPostsCommentsForm: React.FC<Props> = ({
	getInputProps,
	inputList,
	setInputList,
	handleList,
	setHandleList,
}) => {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	return (
		<>
			<TextField
				value={translate(
					"gathers.types.apify_x_simple_searches_posts_comments.create_description.part1"
				)}
			/>
			<Space h="sm" />
			<Text>
				{translate(
					"gathers.types.apify_x_simple_searches_posts_comments.create_description.part2"
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
							"gathers.types.apify_x_simple_searches_posts_comments.create_description.part3a"
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
							"gathers.types.apify_x_simple_searches_posts_comments.create_description.part3b"
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
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.limit_results_per_search"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.limit_results_per_search"
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
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.posts_created_after"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.posts_created_after"
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
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.posts_created_before"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.posts_created_before"
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
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.sort"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.sort"
						)}
					</div>
				}
				{...getInputProps("sort")}
				data={[
					{ label: translate("inputs.select"), value: "" },
					{
						label: translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.sort_options.top"
						),
						value: "Top",
					},
					{
						label: translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.sort_options.latest"
						),
						value: "Latest",
					},
				]}
			/>
			<TextInput
				mt="sm"
				label={
					<div className="flex items-center">
						<Tooltip
							multiline
							width={350}
							label={translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.location"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.location"
						)}
					</div>
				}
				{...getInputProps("location_near")}
			/>
			<TextField
				mt="xl"
				size={30}
				value={translate(
					"gathers.types.apify_x_simple_searches_posts_comments.fields.search_queries"
				)}
			/>
			<Tabs variant="outline" radius="md" defaultValue="info" mt="md">
				<Tabs.List>
					<Tabs.Tab value="info">
						{translate(
							"gathers.types.apify_x_simple_searches_posts_comments.fields.detail"
						)}
					</Tabs.Tab>
					<Tabs.Tab value="keywords">
						<Indicator
							label={`${inputList.length}`}
							disabled={!inputList.length}
							size={16}
						>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.keywords_list"
							)}
						</Indicator>
					</Tabs.Tab>
					<Tabs.Tab value="handles">
						<Indicator
							label={`${handleList.length}`}
							disabled={!handleList.length}
							size={16}
						>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.handle_list"
							)}
						</Indicator>
					</Tabs.Tab>
				</Tabs.List>

				<Tabs.Panel value="info" pt="xs">
					<Group mt="lg" spacing={8}>
						<Text fz="sm">
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part1"
							)}
						</Text>
						<Text fz="sm">
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part2"
							)}
						</Text>
						<Text fz="sm">
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part3"
							)}
						</Text>
						<Text fz="sm">
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part4"
							)}
						</Text>
						<Text fz="sm">
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part5a"
							)}
							<Anchor
								className="font-normal hover:text-blue-500 text-sm underline"
								href={PHEONIX_MANUAL_LINK}
								target="_blank"
							>
								{translate(
									"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part5b"
								)}
							</Anchor>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.fields.info.keyword_handle.part5c"
							)}
						</Text>
					</Group>
				</Tabs.Panel>

				<Tabs.Panel value="keywords" pt="xs">
					<GatherInputs
						label={null}
						placeholder={translate("gathers.fields.input.data_placeholder")}
						data={inputList}
						setData={setInputList}
						split_regex={/[,\n]+/}
						link={false}
						{...getInputProps("keywords_list")}
					/>
				</Tabs.Panel>

				<Tabs.Panel value="handles" pt="xs">
					<GatherInputs
						label={null}
						placeholder={translate("gathers.fields.input.data_placeholder")}
						data={handleList}
						setData={setHandleList}
						split_regex={/[,\n]+/}
						link={false}
						{...getInputProps("handle_list")}
					/>
				</Tabs.Panel>
			</Tabs>
		</>
	);
};

export default ApifyXSimpleSearchesPostsCommentsForm;
