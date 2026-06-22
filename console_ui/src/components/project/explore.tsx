"use client";

import DashboardLinkButton from "@components/buttons/DashboardLinkButton";
import { Anchor, Text, Title } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import React from "react";

const PART_1_LINK =
	"https://www.notion.so/howtobuildup/Gathered-data-output-all-platforms-9bf3ac6ccc824dfca2fe8fa3d7393e64";
const PART_3_LINK =
	"https://www.notion.so/howtobuildup/Visualize-the-data-you-have-gathered-5db82b16367e455f99bda9d13b3fec04";

interface IExploreProps {
	info: any;
}

const ExploreComponent: React.FC<IExploreProps> = ({ info }) => {
	const translate = useTranslate();
	return (
		<div className="p-4 flex flex-col gap-4">
			<Title order={3}>{translate("projects.tabs.explore.title")}</Title>
			<Text fz="sm" mb={4}>
				{translate("projects.tabs.explore.description.part1.a")}
				<Anchor
					className="font-normal text-inherit hover:text-blue-500 text-sm underline"
					href={PART_1_LINK}
					target="_blank"
				>
					{translate("projects.tabs.explore.description.part1.b")}
				</Anchor>
			</Text>
			<Text fz="sm" mb={4}>
				{translate("projects.tabs.explore.description.part2.a")}
				<br />
				{translate("projects.tabs.explore.description.part2.b")}
			</Text>
			<Text fz="sm" mb={4}>
				{translate("projects.tabs.explore.description.part3.a")}
				<Anchor
					className="font-normal text-inherit hover:text-blue-500 text-sm underline"
					href={PART_3_LINK}
					target="_blank"
				>
					{translate("projects.tabs.explore.description.part3.b")}
				</Anchor>
			</Text>
			<DashboardLinkButton
				workspaceSlug={info?.workspace_slug}
				dashboardId={info?.dashboard_id}
			/>
		</div>
	);
};

export default ExploreComponent;
