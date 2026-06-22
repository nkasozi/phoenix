"use client";

import React, { useState, useCallback, useEffect } from "react";
import { Group, Button, Tooltip, Loader, Popover, Text } from "@mantine/core";
import { DateField } from "@refinedev/mantine";
import {
	IconAlertTriangle,
	IconArchive,
	IconCreativeCommonsSa,
	IconPlayerPlay,
} from "@tabler/icons-react";
import Link from "next/link";
import { isJobRunRunning, statusTextStyle } from "src/utils";
import { classifierService } from "src/services";
import { ClassifierResponse } from "src/interfaces/classifier";
import { showNotification } from "@mantine/notifications";
import { useGetLocale } from "@refinedev/core";

interface ClassifierRowProps {
	row: ClassifierResponse;
	refetch: () => void;
	translate: (key: string) => string;
}

const ClassifierRow: React.FC<ClassifierRowProps> = ({
	row,
	refetch,
	translate,
}) => {
	const locale = useGetLocale();
	const currentLocale = locale();
	const [loadingAction, setLoadingAction] = useState(false);
	const {
		id,
		name,
		project_id,
		last_edited_at,
		latest_version,
		latest_job_run,
	} = row;

	const handleArchive = useCallback(async () => {
		setLoadingAction(true);
		try {
			await classifierService.archiveClassifier({
				project_id: row.project_id,
				id: row.id,
			});
			showNotification({
				title: "Success",
				message: translate("classifiers.success.archive"),
			});
			refetch();
		} catch (error: any) {
			showNotification({
				title: "Error",
				message: error?.response?.data?.detail,
			});
			console.error("Error archiving classifier:", error);
		} finally {
			setLoadingAction(false);
		}
	}, [row, refetch, translate]);

	const handleRestore = useCallback(async () => {
		setLoadingAction(true);
		try {
			await classifierService.restoreClassifier({
				project_id: row.project_id,
				id: row.id,
			});
			showNotification({
				title: "Success",
				message: translate("classifiers.success.restore"),
			});
			refetch();
		} catch (error: any) {
			showNotification({
				title: "Error",
				message: error?.response?.data?.detail,
			});
			console.error("Error archiving classifier:", error);
		} finally {
			setLoadingAction(false);
		}
	}, [row, refetch, translate]);

	const status = latest_job_run ? latest_job_run.status : null;
	const type = latest_job_run ? latest_job_run.foreign_job_type : null;

	return (
		<tr>
			<td>
				<div className="flex items-center">
					{(!latest_version ||
						(latest_version &&
							new Date(latest_version?.created_at) <
								new Date(last_edited_at))) && (
						<Tooltip
							multiline
							width={350}
							label={translate("classifiers.caution")}
						>
							<Button p={0} variant="subtle" color="black">
								<IconAlertTriangle size={20} color="black" />
							</Button>
						</Tooltip>
					)}
					<Link
						href={`/projects/${project_id}/classifiers/${row?.type}/${id}`}
						className="no-underline text-blue-500"
					>
						{name}
					</Link>
				</div>
			</td>
			<td>
				{latest_job_run?.started_processing_at && latest_version ? (
					<DateField
						format="LLL"
						value={latest_job_run.started_processing_at}
						locales={currentLocale}
					/>
				) : (
					""
				)}
			</td>
			<td>
				{latest_job_run?.completed_at && latest_version ? (
					<DateField
						format="LLL"
						value={latest_job_run?.completed_at}
						locales={currentLocale}
					/>
				) : (
					"-"
				)}
			</td>
			<td>
				<span className={statusTextStyle(status)}>
					{status ? translate(`status.${type}.${status}`) : "-"}
				</span>
			</td>
			<td>
				<Group spacing="xs" noWrap>
					<>
						{!status && (
							<Tooltip
								label={translate("classifiers.actions.titles.view_and_run")}
							>
								<Button
									component="a"
									p={0}
									href={`/projects/${project_id}/classifiers/${row?.type}/${id}`}
									variant="subtle"
									color="green"
								>
									<IconPlayerPlay size={20} color="green" />
								</Button>
							</Tooltip>
						)}
						{type === "classify_tabulate" &&
							isJobRunRunning(latest_job_run) && <Loader size="sm" />}
						{type === "classifier_archive" &&
							isJobRunRunning(latest_job_run) && <Loader size="sm" />}
						{type === "classifier_restore" &&
							isJobRunRunning(latest_job_run) && <Loader size="sm" />}
						{type === "classify_tabulate" &&
							status === "completed_successfully" && (
								<Popover position="bottom" withArrow shadow="md">
									<Popover.Target>
										<Tooltip
											label={translate("classifiers.actions.titles.archive")}
										>
											<Button p={0} variant="subtle" color="black">
												<IconArchive size={20} color="black" />
											</Button>
										</Tooltip>
									</Popover.Target>
									<Popover.Dropdown>
										<Group className="flex flex-col">
											<Text size="sm" fw={600}>
												{translate("classifiers.actions.text.archive")}
											</Text>
											<Group>
												<Button
													loading={loadingAction}
													onClick={() => {
														handleArchive();
													}}
												>
													{translate("classifiers.actions.button")}
												</Button>
											</Group>
										</Group>
									</Popover.Dropdown>
								</Popover>
							)}
						{type === "classify_tabulate" &&
							!isJobRunRunning(latest_job_run) &&
							status !== "completed_successfully" && (
								<Popover position="bottom" withArrow shadow="md">
									<Popover.Target>
										<Tooltip
											label={translate("classifiers.actions.titles.archive")}
										>
											<Button p={0} variant="subtle" color="black">
												<IconArchive size={20} color="black" />
											</Button>
										</Tooltip>
									</Popover.Target>
									<Popover.Dropdown>
										<Group className="flex flex-col">
											<Text size="sm" fw={600}>
												{translate("classifiers.actions.text.archive")}
											</Text>
											<Group>
												<Button
													loading={loadingAction}
													onClick={() => {
														handleArchive();
													}}
												>
													{translate("classifiers.actions.button")}
												</Button>
											</Group>
										</Group>
									</Popover.Dropdown>
								</Popover>
							)}
						{type === "classifier_archive" &&
							!isJobRunRunning(latest_job_run) &&
							status !== "completed_successfully" && (
								<Popover position="bottom" withArrow shadow="md">
									<Popover.Target>
										<Tooltip
											label={translate("classifiers.actions.titles.archive")}
										>
											<Button p={0} variant="subtle" color="black">
												<IconArchive size={20} color="black" />
											</Button>
										</Tooltip>
									</Popover.Target>
									<Popover.Dropdown>
										<Group className="flex flex-col">
											<Text size="sm" fw={600}>
												{translate("classifiers.actions.text.archive")}
											</Text>
											<Group>
												<Button
													loading={loadingAction}
													onClick={() => {
														handleArchive();
													}}
												>
													{translate("classifiers.actions.button")}
												</Button>
											</Group>
										</Group>
									</Popover.Dropdown>
								</Popover>
							)}
						{type === "classifier_restore" &&
							!isJobRunRunning(latest_job_run) && (
								<Popover position="bottom" withArrow shadow="md">
									<Popover.Target>
										<Tooltip
											label={translate("classifiers.actions.titles.archive")}
										>
											<Button p={0} variant="subtle" color="black">
												<IconArchive size={20} color="black" />
											</Button>
										</Tooltip>
									</Popover.Target>
									<Popover.Dropdown>
										<Group className="flex flex-col">
											<Text size="sm" fw={600}>
												{translate("classifiers.actions.text.archive")}
											</Text>
											<Group>
												<Button
													loading={loadingAction}
													onClick={() => {
														handleArchive();
													}}
												>
													{translate("classifiers.actions.button")}
												</Button>
											</Group>
										</Group>
									</Popover.Dropdown>
								</Popover>
							)}
						{type === "classifier_archive" &&
							status === "completed_successfully" && (
								<Popover position="bottom" withArrow shadow="md">
									<Popover.Target>
										<Tooltip
											label={translate("classifiers.actions.titles.restore")}
										>
											<Button p={0} variant="subtle" color="black">
												<IconCreativeCommonsSa size={20} color="black" />
											</Button>
										</Tooltip>
									</Popover.Target>
									<Popover.Dropdown>
										<Group className="flex flex-col">
											<Text size="sm" fw={600}>
												{translate("classifiers.actions.text.restore")}
											</Text>
											<Group>
												<Button
													loading={loadingAction}
													onClick={() => {
														handleRestore();
													}}
												>
													{translate("classifiers.actions.button")}
												</Button>
											</Group>
										</Group>
									</Popover.Dropdown>
								</Popover>
							)}
					</>
				</Group>
			</td>
		</tr>
	);
};

export default ClassifierRow;
