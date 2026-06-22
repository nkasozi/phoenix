"use client";

import React, { useState, useEffect } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show, TextField, NumberField } from "@refinedev/mantine";
import { Accordion, Container, Group, Space, Title } from "@mantine/core";
import { useParams } from "next/navigation";
import URLInputList from "@components/gather/url-list";
import GatherViewStatus from "@components/gather/view-status";
import GatherViewBreadcrumb from "@components/breadcrumbs/gatherView";
import GatherViewHeaderButton from "@components/gather/header-button";
import GatherViewRun from "@components/gather/view-run";

export default function DanekInstagramCommentsShow(): JSX.Element {
	const { projectid, id } = useParams();
	const [projectInfo, setProjectInfo] = useState({});
	const translate = useTranslate();
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
				value={translate("gathers.types.danek_instagram_comments.view.text")}
			/>
			<Space h="md" />
			<div className="flex gap-4 items-center mb-4">
				<GatherViewHeaderButton
					resource="danek_instagram_comments"
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
									"gathers.types.danek_instagram_comments.view.accordion.status"
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
									"gathers.types.danek_instagram_comments.view.accordion.general"
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
										value={translate("gathers.fields.source.danek")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.fields.platform")}:
									</Title>
									<TextField
										className="capitalize"
										value={translate("gathers.fields.source.instagram")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.fields.data_type")}:
									</Title>
									<TextField
										className="capitalize"
										value={translate("gathers.fields.source.comments")}
									/>
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.danek_instagram_comments.fields.limit_comments_per_post"
										)}
										:
									</Title>
									<NumberField value={record?.limit_comments_per_post} />
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.danek_instagram_comments.fields.limit_child_comments_per_comment"
										)}
										:
									</Title>
									<NumberField
										value={record?.limit_child_comments_per_comment}
									/>
								</Group>
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="source" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"gathers.types.danek_instagram_comments.view.accordion.source"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 flex flex-col my-4">
								<Group>
									<Title my="xs" order={5}>
										{translate(
											"gathers.types.danek_instagram_comments.view.accordion.source_title"
										)}
										:
									</Title>
									{record?.post_id_list?.length}{" "}
									{translate("gathers.fields.source.input_values")}
								</Group>
								{record?.post_id_list?.length > 0 && (
									<URLInputList
										list={record?.post_id_list.map(String)}
										link={false}
									/>
								)}
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
		</Show>
	);
}
