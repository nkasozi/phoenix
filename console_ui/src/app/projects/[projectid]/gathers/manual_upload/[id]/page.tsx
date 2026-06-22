"use client";

import React, { useState } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show, TextField } from "@refinedev/mantine";
import { Accordion, Container, Group, Space, Title } from "@mantine/core";
import { useParams } from "next/navigation";
import GatherViewStatus from "@components/gather/view-status";
import GatherViewBreadcrumb from "@components/breadcrumbs/gatherView";
import Link from "next/link";

export default function ApifyFacebookPostShow(): JSX.Element {
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
		"status",
		"general",
	]);
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
			<TextField value={translate("gathers.types.manual_upload.view.text")} />
			<Space h="md" />
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
					<Accordion.Item value="status" className="mb-4">
						<Accordion.Control>
							<Title order={5}>
								{translate("gathers.types.manual_upload.view.accordion.status")}
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
									"gathers.types.manual_upload.view.accordion.general"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 flex flex-col my-4">
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.types.manual_upload.view.file_name")}:
									</Title>
									<TextField value={record?.uploaded_file_name} />
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.types.manual_upload.view.file_size")}:
									</Title>
									<TextField className="capitalize" value={record?.file_size} />
								</Group>
								<Group>
									<Title my="xs" order={5}>
										{translate("gathers.types.manual_upload.view.no_rows")}:
									</Title>
									<TextField
										className="capitalize"
										value={record?.file_row_count}
									/>
								</Group>
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
		</Show>
	);
}
