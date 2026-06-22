"use client";

import React, { useState } from "react";
import { useTranslate, useList } from "@refinedev/core";
import { Group, Button, Text, Title, Anchor, Space } from "@mantine/core";
import { IconSquarePlus } from "@tabler/icons-react";
import GatherDeleteModal from "@components/modals/delete-gather";
import Link from "next/link";
import GatherTable from "@components/table/GatherTable";
import { projectHasRemainingCredits } from "src/utils";

const PHEONIX_MANUAL_GATHER =
	"https://howtobuildup.notion.site/Decide-where-you-will-get-data-from-167f039d54874316be086734be194654";
const PHEONIX_MANUAL_GATHER_MORE =
	"https://howtobuildup.notion.site/Understanding-platform-credits-3f749bc6ebdf4ca68ba44447bc0dd4cc";

interface IGatherProps {
	project: any;
	refetch: any;
}

const GatherComponent: React.FC<IGatherProps> = ({
	project,
	refetch: projectRefetch,
}) => {
	const translate = useTranslate();
	const [deleteModalOpen, setDeleteModalOpen] = useState(false);
	const [selected, setSelected] = useState(null);

	const migratedApiResponse: any = useList({
		resource: project?.id ? `projects/${project.id}/gathers` : "",
		pagination: {
			mode: "off",
		},
	});

	const apiResponse = {
		...migratedApiResponse.result,
		...migratedApiResponse.query,
		...migratedApiResponse,
	};

	const { refetch: gatherRefetch } = apiResponse;

	const refetch = () => {
		projectRefetch();
		gatherRefetch();
	};

	return (
		<>
			<div className="p-4">
				<div className="flex flex-col gap-4">
					<Title order={3}>{translate("projects.tabs.gather.title")}</Title>
					<Text fz="sm">
						{translate("projects.tabs.gather.description.part1.a")}
						<Anchor
							className="font-normal hover:text-blue-500 text-sm underline"
							href={PHEONIX_MANUAL_GATHER}
							target="_blank"
						>
							{translate("projects.tabs.gather.description.part1.b")}
						</Anchor>
						{translate("projects.tabs.gather.description.part1.c")}
					</Text>
					<Text fz="sm">
						{translate("projects.tabs.gather.description.part2.a")}
						<Anchor
							className="font-normal hover:text-blue-500 text-sm underline"
							href={PHEONIX_MANUAL_GATHER_MORE}
							target="_blank"
						>
							{translate("projects.tabs.gather.description.part2.b")}
						</Anchor>
						{translate("projects.tabs.gather.description.part2.c")}
					</Text>
				</div>
				<Space h="md" />
				<Link
					href={
						projectHasRemainingCredits(project)
							? `/projects/${project?.id}/gathers/select_type`
							: "#"
					}
				>
					<Button
						leftIcon={<IconSquarePlus />}
						disabled={!projectHasRemainingCredits(project)}
					>
						{translate("actions.create")}
					</Button>
				</Link>
				<Space h="md" />
				<GatherTable
					data={apiResponse.data?.data}
					setSelected={setSelected}
					setDeleteModalOpen={setDeleteModalOpen}
				/>
			</div>
			<GatherDeleteModal
				opened={deleteModalOpen}
				setOpened={setDeleteModalOpen}
				gatherDetail={selected}
				refetch={refetch}
			/>
		</>
	);
};

export default GatherComponent;
