"use client";

import React, { useState, useEffect } from "react";
import {
	useGetLocale,
	useResourceParams,
	useShow,
	useTranslate,
} from "@refinedev/core";
import {
	Show,
	TextField,
	DateField,
	EditButtonProps,
	EditButton,
} from "@refinedev/mantine";
import { Alert, Group, Loader, Tabs, Text, Title } from "@mantine/core";
import OverviewComponent from "@components/project/overview";
import AboutComponent from "@components/project/about";
import ExploreComponent from "@components/project/explore";
import GatherComponent from "@components/project/gather";
import ClassifyComponent from "@components/project/classify";
import { useRouter, useSearchParams } from "next/navigation";
import { projectHasRemainingCredits } from "src/utils";
import Link from "next/link";

export default function ProjectShow(): JSX.Element {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	const { query } = useShow();
	const router = useRouter();
	const searchParams = useSearchParams();
	const activeItem = searchParams.get("activeItem");
	const { refetch, data, isLoading } = query;

	const record = data?.data;

	const { id: idFromParams, identifier } = useResourceParams({
		resource: "projects",
	});
	const [activeTab, setActiveTab] = useState<string | null>(
		activeItem || "overview"
	);

	const editButtonProps: EditButtonProps = {
		...(isLoading ? { disabled: true } : {}),
		// color: "primary",
		variant: "outline",
		resource: identifier,
		recordItemId: idFromParams,
	};
	useEffect(() => {
		if (activeItem) {
			setActiveTab(activeItem);
		}
	}, [activeItem]);
	return (
		<Show
			title={<Title order={3}>{record?.name}</Title>}
			isLoading={isLoading}
			headerButtons={() => <EditButton {...editButtonProps} />}
		>
			<TextField value={record?.description} />

			<Group>
				<Title my="xs" order={5}>
					{translate("projects.dataset_last_update")}:
				</Title>
				{record?.last_job_run_completed_at ? (
					<DateField
						format="LLL"
						value={record?.last_job_run_completed_at}
						locales={currentLocale}
					/>
				) : (
					<Text>-</Text>
				)}
				{record?.latest_job_run && !record?.latest_job_run?.completed_at && (
					<Loader size="xs" />
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{record?.has_unlimited_credits
						? translate("projects.total_costs")
						: translate("projects.total_costs_and_allocated_credits")}
					:
				</Title>
				<Text>
					{record?.total_costs.toFixed(2)}
					{record &&
						!record?.has_unlimited_credits &&
						` / ${record.total_allocated_credits.toFixed(2)}`}
				</Text>
				{record?.latest_job_run?.completed_at === null && <Loader size="xs" />}
			</Group>
			{!projectHasRemainingCredits(record) && (
				<Group>
					<Text color="red" weight={500}>
						{translate("projects.no_more_allocated_credits")}
					</Text>
				</Group>
			)}
			{record && record.project_resources_provisioned_at === null && (
				<Alert
					color="yellow"
					title={translate("projects.resources_provisioning_title")}
					my="md"
				>
					{translate("projects.resources_provisioning_message")}
				</Alert>
			)}
			<Tabs
				value={activeTab}
				onTabChange={(value) =>
					router.replace(`/projects/show/${idFromParams}?activeItem=${value}`)
				}
			>
				<Tabs.List>
					<Tabs.Tab value="overview">
						{translate("projects.tabs.overview.header")}
					</Tabs.Tab>
					<Tabs.Tab value="gather">
						{translate("projects.tabs.gather.header")}
					</Tabs.Tab>
					<Tabs.Tab value="classify">
						{translate("projects.tabs.classify.header")}
					</Tabs.Tab>
					<Tabs.Tab value="explore">
						{translate("projects.tabs.explore.header")}
					</Tabs.Tab>
					<Tabs.Tab value="about">
						{translate("projects.tabs.about.header")}
					</Tabs.Tab>
					<div className="cursor-pointer border-t-2 hover:border-[#dee2e6] hover:bg-[#f8f9fa] px-4 py-2.5 text-sm border-b-2">
						<Link
							className="no-underline text-black"
							href="https://www.notion.so/howtobuildup/4ee4530d67574fb5a81ff55c7be348f9?v=4b66998dcd1a4ad283293e6c6deb3c13"
							target="_blank"
						>
							{translate("projects.tabs.help.header")}
						</Link>
					</div>
				</Tabs.List>

				<Tabs.Panel value="overview" pt="xs">
					<OverviewComponent setActiveTab={setActiveTab} info={record} />
				</Tabs.Panel>

				<Tabs.Panel value="gather" pt="xs">
					<GatherComponent project={record} refetch={refetch} />
				</Tabs.Panel>

				<Tabs.Panel value="classify" pt="xs">
					<ClassifyComponent project={record} refetch={refetch} />
				</Tabs.Panel>

				<Tabs.Panel value="explore" pt="xs">
					<ExploreComponent info={record} />
				</Tabs.Panel>

				<Tabs.Panel value="about" pt="xs">
					<AboutComponent info={record} />
				</Tabs.Panel>
			</Tabs>
		</Show>
	);
}
