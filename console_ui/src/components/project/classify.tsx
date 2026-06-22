"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useTranslate, useList } from "@refinedev/core";
import {
	Group,
	Button,
	Text,
	Title,
	Anchor,
	Loader,
	Space,
} from "@mantine/core";
import { IconSquarePlus } from "@tabler/icons-react";
import Link from "next/link";
import ClassifierTable from "@components/table/ClassifyTable";
import { gatherService } from "src/services";

const PHEONIX_MANUAL_CLASSIFIER =
	"https://howtobuildup.notion.site/Decide-how-you-want-to-classify-data-43a8b3a25fd84eadaa67a03dd8b06175";

interface IClassifierProps {
	project: any;
	refetch: any;
}

const ClassifyComponent: React.FC<IClassifierProps> = ({
	project,
	refetch: projectRefetch,
}) => {
	const translate = useTranslate();
	const [loading, setLoading] = useState(true);
	const [hasGathered, setHasGathered] = useState(false);
	const [classifierList, setClassifierList] = useState<any>([]);

	const migratedApiResponse: any = useList({
		resource: project?.id ? `projects/${project.id}/classifiers` : "",
		pagination: {
			mode: "off",
		},
	});

	const apiResponse = useMemo(
		() => ({
			...migratedApiResponse.result,
			...migratedApiResponse.query,
			...migratedApiResponse,
		}),
		[migratedApiResponse]
	);

	const { refetch: classifyRefetch, isLoading } = apiResponse;

	const refetch = () => {
		projectRefetch();
		classifyRefetch();
	};

	const checkGathers = async (): Promise<void> => {
		const gatherList = await gatherService.gatherList(project.id);
		setHasGathered(
			gatherList?.data.some(
				(item: any) => item.latest_job_run?.status === "completed_successfully"
			)
		);
		setLoading(false);
	};

	useEffect(() => {
		setLoading(true);
		if (project?.id) checkGathers();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [project]);

	useEffect(() => {
		if (apiResponse?.data?.data) {
			setClassifierList(apiResponse.data.data);
		}
	}, [apiResponse?.data?.data]);

	useEffect(() => {
		let interval: NodeJS.Timeout | undefined;
		if (
			classifierList.some(
				(classifier: any) =>
					!classifier.latest_job_run?.completed_at ||
					(classifier.delete_job_run &&
						!classifier.delete_job_run?.completed_at)
			)
		) {
			interval = setInterval(() => {
				const pendingClassifiers = classifierList.filter(
					(classifier: any) =>
						classifier.latest_job_run &&
						!classifier.latest_job_run?.completed_at
				);
				if (pendingClassifiers.length > 0) apiResponse?.refetch();
			}, 10000);
		}
		return () => {
			if (interval) {
				clearInterval(interval);
			}
		};
	}, [classifierList, apiResponse]);

	if (loading || isLoading) {
		return (
			<div className="min-h-80 flex justify-center items-center">
				<Loader />
			</div>
		);
	}
	return hasGathered ? (
		<div className="p-4">
			<div className="flex flex-col gap-4">
				<Title order={3}>{translate("projects.tabs.classifier.title")}</Title>
				<Text fz="sm">
					{translate("projects.tabs.classifier.description.part1.a")}
				</Text>
				<Text fz="md" fw={700}>
					{translate("projects.tabs.classifier.description.part1.b")}
				</Text>
				<Text fz="sm">
					{translate("projects.tabs.classifier.description.part1.c")}
					<Anchor
						className="font-normal hover:text-blue-500 text-sm underline"
						href={PHEONIX_MANUAL_CLASSIFIER}
						target="_blank"
					>
						{translate("projects.tabs.classifier.description.part1.d")}
					</Anchor>
					{translate("projects.tabs.classifier.description.part1.e")}
				</Text>
			</div>
			<Space h="md" />
			<Link href={`/projects/${project?.id}/classifiers/select_type`}>
				<Button leftIcon={<IconSquarePlus />}>
					{translate("actions.create")}
				</Button>
			</Link>
			<Space h="md" />
			<ClassifierTable refetch={refetch} data={classifierList} />
		</div>
	) : (
		<div className="p-4">
			<Group className="mb-4">
				<div className="flex flex-col gap-4">
					<Title order={3}>{translate("projects.tabs.classifier.title")}</Title>
					<Text fz="sm">{translate("classifiers.no_gather.text1")}</Text>
					<Text fz="sm">{translate("classifiers.no_gather.text2")}</Text>
					<Text fz="sm">
						{translate("classifiers.no_gather.text3a")}
						<Anchor
							className="font-normal text-inherit hover:text-blue-500 text-sm underline"
							href={PHEONIX_MANUAL_CLASSIFIER}
							target="_blank"
						>
							{translate("classifiers.no_gather.text3b")}
						</Anchor>
						{translate("classifiers.no_gather.text3c")}
					</Text>
				</div>
			</Group>
		</div>
	);
};

export default ClassifyComponent;
