"use client";

import React, { useState } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show } from "@refinedev/mantine";
import { Accordion, Container, Switch, Title } from "@mantine/core";
import { useParams } from "next/navigation";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import ClassifierViewStatus from "@components/classifier/view-status";
import ClassifierViewGeneral from "@components/classifier/view-general";
import ClassifierViewHeader from "@components/classifier/view-header";

export default function PerspectiveApiClassifierShow(): JSX.Element {
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
		"classes",
	]);

	const classes: any = {
		toxicity: "Toxicity",
		severe_toxicity: "Severe Toxicity",
		identity_attack: "Identity Attack",
		insult: "Insult",
		threat: "Threat",
		sexually_explicit: "Sexually Explicit",
		flirtation: "Flirtation",
	};

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
									"classifiers.types.perspective_api.view.accordion.status"
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
									"classifiers.types.perspective_api.view.accordion.general"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<ClassifierViewGeneral record={record} />
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="classes" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"classifiers.types.perspective_api.view.accordion.classes"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 my-4 space-y-4 w-64">
								{record?.latest_version?.params &&
									Object.keys(record?.latest_version?.params).map(
										(category, idx) => {
											const categoryData =
												record?.latest_version?.params[category];

											return (
												<Switch
													key={idx}
													labelPosition="left"
													size="lg"
													radius="md"
													className="justify-between"
													label={classes[category]}
													checked={categoryData.enabled}
													disabled
												/>
											);
										}
									)}
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
		</Show>
	);
}
