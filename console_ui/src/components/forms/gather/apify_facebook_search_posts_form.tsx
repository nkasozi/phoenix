"use client";

import React, { Dispatch, SetStateAction } from "react";
import {
	Alert,
	Button,
	Checkbox,
	Group,
	NumberInput,
	Select,
	TextInput,
	Tooltip,
} from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import { TextField } from "@refinedev/mantine";
import { countryList } from "src/utils/constants";

const today = new Date();
const tomorrow = new Date(today);
tomorrow.setDate(tomorrow.getDate() + 1);

export const initialFormValues = {
	name: "",
	search_query: "",
	limit_posts: 10,
	limit_retries: 1,
	recent_posts: true,
};

// Define separate validation rules for posts
export function getPostValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate(
					"gathers.types.apify_facebook_search_posts.fields.validation.required"
				)
			: null;
	validationRules.search_query =
		data.search_query.length <= 0
			? translate(
					"gathers.types.apify_facebook_search_posts.fields.validation.required"
				)
			: null;
	validationRules.limit_posts =
		data.limit_posts === undefined || data.limit_posts <= 0
			? translate(
					"gathers.types.apify_facebook_search_posts.fields.validation.required"
				)
			: null;
	validationRules.limit_retries =
		data.limit_retries === undefined || data.limit_retries <= 0
			? translate(
					"gathers.types.apify_facebook_search_posts.fields.validation.required"
				)
			: null;

	return validationRules;
}

export const getUpdatedFormValues = (
	formValues: any,
	proxyGroup: string,
	proxyCountry: string | null
) => ({
	...formValues,
	proxy: {
		use_apify_proxy: proxyGroup === "RESIDENTIAL",
		apify_proxy_groups:
			proxyGroup === "RESIDENTIAL" ? ["RESIDENTIAL"] : undefined,
		apify_proxy_country:
			proxyGroup === "RESIDENTIAL" && proxyCountry !== ""
				? proxyCountry
				: undefined,
	},
});

interface Props {
	proxyCountry: string | null;
	setProxyCountry: Dispatch<SetStateAction<string | null>>;
	getInputProps: GetInputProps<ProjectSchema>;
}

const ApifyFacebookSearchPostsForm: React.FC<Props> = ({
	getInputProps,
	proxyCountry,
	setProxyCountry,
}) => {
	const translate = useTranslate();
	return (
		<>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.apify_facebook_search_posts.create_description.part1"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.apify_facebook_search_posts.create_description.part2"
				)}
			/>
			<TextField
				mb="sm"
				value={translate(
					"gathers.types.apify_facebook_search_posts.create_description.part3"
				)}
			/>
			<TextField
				mb="lg"
				value={translate(
					"gathers.types.apify_facebook_search_posts.create_description.part4"
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
			<TextInput
				className="flex-1"
				mt="sm"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_search_posts.fields.info.search_query"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_search_posts.fields.search_query"
						)}
					</div>
				}
				{...getInputProps("search_query")}
			/>
			<Button
				component="a"
				className="!bg-transparent"
				href={`https://www.facebook.com/search/posts?q=${getInputProps("search_query").value}`}
				target="_blank"
				rel="noopener noreferrer"
				p={0}
				disabled={!getInputProps("search_query").value}
				variant="subtle"
			>
				{translate(
					"gathers.types.apify_facebook_search_posts.fields.info.search_query_results"
				)}
				<Tooltip
					label={translate(
						"gathers.types.apify_facebook_search_posts.fields.info.results_tooltip"
					)}
				>
					<span className="flex">
						<IconInfoCircle size={12} />
					</span>
				</Tooltip>
			</Button>
			<NumberInput
				mt="lg"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_search_posts.fields.info.limit_posts"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_search_posts.fields.limit_posts"
						)}
					</div>
				}
				{...getInputProps("limit_posts")}
			/>
			<NumberInput
				mt="lg"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"gathers.types.apify_facebook_search_posts.fields.info.limit_retries"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate(
							"gathers.types.apify_facebook_search_posts.fields.limit_retries"
						)}
					</div>
				}
				{...getInputProps("limit_retries")}
			/>
			<Checkbox
				mt="lg"
				label={
					<div className="flex items-center">
						{translate(
							"gathers.types.apify_facebook_search_posts.fields.recent_posts"
						)}
						<Tooltip
							width={350}
							multiline
							label={translate(
								"gathers.types.apify_facebook_search_posts.fields.info.recent_posts"
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
			<div>
				<Group spacing="lg" mt="lg">
					<Select
						label={
							<div className="flex items-center">
								<Tooltip
									width={350}
									multiline
									label={translate(
										"gathers.types.apify_facebook_search_posts.fields.info.proxy_groups"
									)}
								>
									<span className="flex">
										<IconInfoCircle size={12} />
									</span>
								</Tooltip>
								{translate(
									"gathers.types.apify_facebook_search_posts.fields.proxy_groups"
								)}
							</div>
						}
						value={proxyCountry || ""}
						onChange={setProxyCountry}
						data={[
							{
								value: "",
								label: translate(
									"gathers.types.apify_facebook_search_posts.fields.anywhere"
								),
							},
							...countryList.filter((country) => country.value !== "None"),
						]}
					/>
				</Group>
			</div>
			<Alert mt="lg" title={translate("note")} color="orange">
				{translate("gathers.types.apify_facebook_search_posts.warnings.create")}
			</Alert>
		</>
	);
};

export default ApifyFacebookSearchPostsForm;
