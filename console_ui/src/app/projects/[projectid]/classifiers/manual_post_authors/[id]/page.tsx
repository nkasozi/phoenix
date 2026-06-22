"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useShow, useTranslate } from "@refinedev/core";
import { Show } from "@refinedev/mantine";
import {
	Accordion,
	Button,
	Container,
	ScrollArea,
	Table,
	Title,
} from "@mantine/core";
import { useParams } from "next/navigation";
import { IconExternalLink } from "@tabler/icons-react";
import { classifierService } from "src/services";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import ClassifierViewStatus from "@components/classifier/view-status";
import ClassifierViewGeneral from "@components/classifier/view-general";
import PaginationComponent from "@components/table/pagination";
import { getAuthorProfileLink } from "src/utils";
import ClassifierRunModal from "@components/modals/classifier-run";
import ClassifierViewHeader from "@components/classifier/view-header";
import { Author } from "../model";

export default function ManualPostClassifierShow(): JSX.Element {
	const { projectid, id } = useParams();
	const translate = useTranslate();
	const [opened, setOpened] = useState(false);
	const [authors, setAuthors] = useState<Author[]>([]);
	const [totalAuthors, setTotalAuthors] = useState(0);
	const [activePage, setActivePage] = useState(1);
	const authorsPerPage = 10; // Set the number of authors to show per page
	const { query } = useShow({
		resource: `projects/${projectid}/classifiers`,
		id: id as string,
	});

	const { data, isLoading, refetch } = query;

	const record = data?.data;

	const [accordionValue, setAccordionValue] = useState<string[]>([
		"status",
		"general",
		"classes",
		"authors",
	]);

	// Fetch initial data on mount
	const fetchData = useCallback(
		async (page: number) => {
			const start = (page - 1) * authorsPerPage;
			const end = start + authorsPerPage;
			try {
				const authorsResponse = await classifierService.getManualPostAuthors({
					project_id: projectid as string,
					classifier_id: id as string,
					params: { start, end },
				});
				setAuthors(authorsResponse?.data?.authors);
				setTotalAuthors(authorsResponse?.data?.meta?.total_count);
			} catch (error) {
				console.error("Error fetching classifier data", error);
			}
		},
		[id, projectid, setAuthors]
	);

	useEffect(() => {
		if (id && projectid) {
			fetchData(activePage);
		}
	}, [id, projectid, activePage, fetchData]);

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
									"classifiers.types.manual_post_authors.view.accordion.status"
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
									"classifiers.types.manual_post_authors.view.accordion.general"
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
									"classifiers.types.manual_post_authors.view.accordion.class_configuration"
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
										</tr>
									</thead>
									<tbody>
										{record?.intermediatory_classes?.map(
											(classItem: any, classIndex: number) => (
												<tr key={classIndex}>
													<td className="align-baseline">{classItem?.name}</td>
													<td className="align-baseline">
														{classItem?.description}
													</td>
												</tr>
											)
										)}
									</tbody>
								</Table>
							</Container>
						</Accordion.Panel>
					</Accordion.Item>
					<Accordion.Item value="authors" mb="md">
						<Accordion.Control>
							<Title order={5}>
								{translate(
									"classifiers.types.manual_post_authors.view.accordion.author_configuration"
								)}
							</Title>
						</Accordion.Control>
						<Accordion.Panel>
							<Container className="mx-0 flex flex-col my-4">
								<ScrollArea>
									<Table highlightOnHover withBorder>
										<thead>
											<tr>
												<th>
													{translate(
														"classifiers.types.manual_post_authors.fields.classes"
													)}
												</th>
												<th>
													{translate(
														"classifiers.types.manual_post_authors.fields.author_name"
													)}
												</th>
												<th>
													{translate(
														"classifiers.types.manual_post_authors.fields.no_of_posts"
													)}
												</th>
												<th>
													{translate(
														"classifiers.types.manual_post_authors.fields.author_platform"
													)}
												</th>
												<th>
													{translate(
														"classifiers.types.manual_post_authors.fields.author_anon_id"
													)}
												</th>
											</tr>
										</thead>
										<tbody>
											{authors.map((author) => (
												<tr key={author.phoenix_platform_message_author_id}>
													<td>
														<div className="flex flex-wrap">
															{author.intermediatory_author_classes.map(
																(cls) => (
																	<span
																		key={cls.class_id}
																		className="mr-2 mb-2 px-2 py-1 bg-gray-200 rounded text-sm sm:text-base"
																	>
																		{cls.class_name}
																	</span>
																)
															)}
														</div>
													</td>
													<td>
														{author.pi_platform_message_author_name}
														&nbsp;
														<Button
															component="a"
															href={getAuthorProfileLink(author)}
															target="_blank"
															rel="noopener noreferrer"
															p={0}
															variant="subtle"
														>
															<IconExternalLink size={20} />
														</Button>
													</td>
													<td>{author.post_count}</td>
													<td className="capitalize">{author.platform}</td>
													<td>{author.pi_platform_message_author_id}</td>
												</tr>
											))}
										</tbody>
									</Table>
								</ScrollArea>
								<br />
								<PaginationComponent
									pages={Math.ceil(totalAuthors / authorsPerPage)}
									_activeIndex={activePage}
									_setActiveIndex={setActivePage}
								/>
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
