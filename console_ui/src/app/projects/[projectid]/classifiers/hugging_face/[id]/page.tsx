"use client";

import React, { useState } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show } from "@refinedev/mantine";
import { Accordion, Title } from "@mantine/core";
import { useParams } from "next/navigation";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import ClassifierViewStatus from "@components/classifier/view-status";
import ClassifierViewGeneral from "@components/classifier/view-general";
import ClassifierViewHeader from "@components/classifier/view-header";

export default function HuggingFaceClassifierShow(): JSX.Element {
	const { projectid, id } = useParams();
	const translate = useTranslate();
	const { query } = useShow({
		resource: `projects/${projectid}/classifiers`,
		id: id as string,
	});

	const { data, isLoading } = query;

	const record = data?.data;

	const [accordionValue, setAccordionValue] = useState<string[]>([
		"status",
		"general",
	]);

	return (
		<Show
			title={<Title order={3}>{record?.name}</Title>}
			breadcrumb={
				<ClassifierViewBreadcrumb
					record={record}
					projectid={projectid as string}
				/>
			}
			isLoading={isLoading}
			headerButtons={() => null}
		>
			<ClassifierViewHeader
				id={id as string}
				record={record}
				setOpened={() => {}}
			/>
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
								{translate(
									"classifiers.types.hugging_face.view.accordion.status"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<ClassifierViewStatus record={record} />
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="general" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"classifiers.types.hugging_face.view.accordion.general"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<ClassifierViewGeneral record={record} />
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
		</Show>
	);
}
