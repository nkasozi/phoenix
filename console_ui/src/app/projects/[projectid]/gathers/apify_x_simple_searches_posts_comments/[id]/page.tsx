"use client";

import React, { useState, useEffect } from "react";
import { useGetLocale, useShow, useTranslate } from "@refinedev/core";
import { Show, TextField, DateField, NumberField } from "@refinedev/mantine";
import {
	Accordion,
	Container,
	Flex,
	Group,
	Indicator,
	Space,
	Tabs,
	Title,
} from "@mantine/core";
import { useParams } from "next/navigation";
import URLInputList from "@components/gather/url-list";
import GatherViewStatus from "@components/gather/view-status";
import GatherViewBreadcrumb from "@components/breadcrumbs/gatherView";
import GatherViewHeaderButton from "@components/gather/header-button";
import GatherViewRun from "@components/gather/view-run";
import { xAdvancedSearchBaseLink } from "src/utils/constants";
import ComputedSearchesURLs from "@components/gather/computed-searches-list";

export default function ApifyXAdvancedSearchShow(): JSX.Element {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	const { projectid, id } = useParams();
	const [projectInfo, setProjectInfo] = useState({});
	const { query } = useShow({
		resource: `projects/${projectid}/gathers`,
		id: id as string,
	});

	const { data, isLoading, refetch } = query;

	const record = data?.data;

	const [accordionValue, setAccordionValue] = useState<string[]>([
		"general",
		"source",
	]);

	useEffect(() => {
		if (!record) return;
		if (record?.latest_job_run != null) {
			setAccordionValue(["status", "general", "source"]);
		} else {
			setAccordionValue(["run", "general", "source"]);
		}
	}, [record]);

	return (
		<Show
			title={<Title order={3}>{record?.name}</Title>}
			breadcrumb={
				<GatherViewBreadcrumb
					record={record}
					projectid={projectid as string}
					setProjectInfo={setProjectInfo}
				/>
			}
			isLoading={isLoading}
			headerButtons={() => null}
		>
			<TextField
				value={translate(
					"gathers.types.apify_x_simple_searches_posts_comments.view.text"
				)}
			/>
			<Space h="md" />
			<div className="flex gap-4 items-center mb-4">
				<GatherViewHeaderButton
					resource="apify_x_simple_searches_posts_comments"
					id={id as string}
					projectid={projectid as string}
					record={record}
					isLoading={isLoading}
				/>
			</div>
			<div className="w-full">
				<Accordion
					styles={{
						control: {
							paddingLeft: 0,
						},
						item: {
							"&[data-active]": {
								backgroundColor: "none",
							},
						},
					}}
					multiple
					value={accordionValue}
					onChange={setAccordionValue}
				>
					<Accordion.Item value="run" className="mb-4">
						<Accordion.Control>
							<Title order={5}>{translate("gathers.actions.titles.run")}</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<GatherViewRun
								record={record}
								refetch={refetch}
								projectInfo={projectInfo}
							/>
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="status" className="mb-4">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"gathers.types.apify_x_simple_searches_posts_comments.view.accordion.status"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<GatherViewStatus record={record} />
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="general" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"gathers.types.apify_x_simple_searches_posts_comments.view.accordion.general"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 flex flex-col my-4">
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.fields.from")}:
									</Title>
									<TextField
										className="capitalize"
										value={translate("gathers.fields.source.apify")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.fields.platform")}:
									</Title>
									<TextField
										className="capitalize"
										value={translate("gathers.fields.source.x")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.fields.data_type")}:
									</Title>
									<TextField
										className="capitalize"
										value={translate("gathers.fields.source.posts_comments")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.apify_x_simple_searches_posts_comments.fields.posts_created_after"
										)}
										:
									</Title>
									<DateField
										format="LLL"
										value={record?.posts_created_after}
										locales={currentLocale}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.apify_x_simple_searches_posts_comments.fields.posts_created_before"
										)}
										:
									</Title>
									<DateField
										format="LLL"
										value={record?.posts_created_before}
										locales={currentLocale}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.apify_x_simple_searches_posts_comments.fields.limit_results_per_search"
										)}
										:
									</Title>
									<NumberField value={record?.limit_results_per_search} />
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.apify_x_simple_searches_posts_comments.fields.sort"
										)}
										:
									</Title>
									<TextField
										className="capitalize"
										value={translate(
											`gathers.types.apify_x_simple_searches_posts_comments.fields.sort_options.${record?.sort?.toLowerCase()}`
										)}
									/>
								</Group>
								{record?.location_near && (
									<Group>
										<Title my="xs" order={5}>
											{translate(
												"gathers.types.apify_x_simple_searches_posts_comments.fields.location"
											)}
											:
										</Title>
										<TextField
											className="capitalize"
											value={record?.location_near || "-"}
										/>
									</Group>
								)}
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="source" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"gathers.types.apify_x_simple_searches_posts_comments.view.accordion.source"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Tabs
								variant="outline"
								radius="md"
								defaultValue="computed"
								mt="md"
							>
								<Tabs.List>
									<Tabs.Tab value="computed">
										<Indicator
											label={`${record?.search_list?.length}`}
											disabled={!record?.search_list?.length}
											size={16}
										>
											{translate(
												"gathers.types.apify_x_simple_searches_posts_comments.view.computed.title"
											)}
										</Indicator>
									</Tabs.Tab>
									<Tabs.Tab value="keywords">
										<Indicator
											label={`${record?.keywords_list?.length}`}
											disabled={!record?.keywords_list?.length}
											size={16}
										>
											{translate(
												"gathers.types.apify_x_simple_searches_posts_comments.fields.keywords_list"
											)}
										</Indicator>
									</Tabs.Tab>
									<Tabs.Tab value="handles">
										<Indicator
											label={`${record?.handle_list?.length}`}
											disabled={!record?.handle_list?.length}
											size={16}
										>
											{translate(
												"gathers.types.apify_x_simple_searches_posts_comments.fields.handle_list"
											)}
										</Indicator>
									</Tabs.Tab>
								</Tabs.List>

								<Tabs.Panel value="computed" pt="xs">
									{record?.search_list?.length > 0 && (
										<ComputedSearchesURLs
											template_url_for_input={xAdvancedSearchBaseLink}
											list={record?.search_list}
										/>
									)}
								</Tabs.Panel>
								<Tabs.Panel value="keywords" pt="xs">
									{record?.keywords_list?.length > 0 && (
										<URLInputList link={false} list={record?.keywords_list} />
									)}
								</Tabs.Panel>

								<Tabs.Panel value="handles" pt="xs">
									{record?.handle_list?.length > 0 && (
										<URLInputList link={false} list={record?.handle_list} />
									)}
								</Tabs.Panel>
							</Tabs>
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
		</Show>
	);
}
