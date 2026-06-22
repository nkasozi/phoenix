"use client";

import React, { Fragment, useState } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show } from "@refinedev/mantine";
import { Accordion, ActionIcon, Container, Table, Title } from "@mantine/core";
import { useParams } from "next/navigation";
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import ClassifierViewStatus from "@components/classifier/view-status";
import ClassifierViewGeneral from "@components/classifier/view-general";
import ClassifierRunModal from "@components/modals/classifier-run";
import ClassifierViewHeader from "@components/classifier/view-header";
import KeywordTableView from "./KeywordTableView";

export default function KeywordClassifierShow(): JSX.Element {
	const { projectid, id } = useParams();
	const [opened, setOpened] = useState(false);
	const translate = useTranslate();
	const [openRows, setOpenRows] = useState<{ [key: number]: boolean }>({});
	const { query } = useShow({
		resource: `projects/${projectid}/classifiers`,
		id: id as string,
	});

	const { data, isLoading, refetch } = query;

	const record = data?.data;

	const [accordionValue, setAccordionValue] = useState<string[]>([
		"status",
		"general",
		"configuration",
	]);

	const toggleRow = (index: number) => {
		setOpenRows((prev) => ({ ...prev, [index]: !prev[index] }));
	};

	const getClassKeywordGroups = (classItem: any) =>
		record?.intermediatory_class_to_keyword_configs?.filter(
			(group: any) => group.class_id === classItem?.id
		) || [];

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
				setOpened={setOpened}
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
									"classifiers.types.keyword_match.view.accordion.status"
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
									"classifiers.types.keyword_match.view.accordion.general"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<ClassifierViewGeneral record={record} />
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="configuration" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"classifiers.types.keyword_match.view.accordion.configuration"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 flex flex-col my-4">
								<Table highlightOnHover withBorder>
									<thead>
										<tr>
											<th>{translate("classifiers.fields.class_name")}</th>
											<th>{translate("projects.fields.description")}</th>
											<th className="text-center" style={{ width: "120px" }}>
												{translate("classifiers.fields.keyword_count")}
											</th>
											<th style={{ width: "100px" }} />
										</tr>
									</thead>
									<tbody>
										{record?.intermediatory_classes?.map(
											(classItem: any, classIndex: number) => {
												const classKeywordGroups =
													getClassKeywordGroups(classItem);
												return (
													<Fragment key={classIndex}>
														<tr>
															<td className="align-baseline">
																{classItem?.name}
															</td>
															<td className="align-baseline">
																{classItem?.description}
															</td>
															<td className="align-baseline text-center">
																{classKeywordGroups.length}
															</td>
															<td className="align-baseline">
																<div className="flex gap-1 items-center justify-center">
																	{classKeywordGroups.length > 0 && (
																		<ActionIcon
																			color="dark"
																			variant="light"
																			onClick={() => toggleRow(classIndex)}
																		>
																			{openRows[classIndex] ? (
																				<IconChevronUp size={16} />
																			) : (
																				<IconChevronDown size={16} />
																			)}
																		</ActionIcon>
																	)}
																</div>
															</td>
														</tr>
														{openRows[classIndex] && (
															<KeywordTableView
																keywordGroups={classKeywordGroups}
																translate={translate}
															/>
														)}
													</Fragment>
												);
											}
										)}
									</tbody>
								</Table>
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
				</Accordion>
			</div>
			<ClassifierRunModal
				opened={opened}
				setOpened={setOpened}
				classifierDetail={record}
				refetch={refetch}
			/>
		</Show>
	);
}
