// GatherRow.tsx
import React, { useState, useCallback, useEffect } from "react";
import { Group, Button, Tooltip, Loader, Text } from "@mantine/core";
import { DateField } from "@refinedev/mantine";
import {
	IconAlertTriangle,
	IconPlayerPlay,
	IconTrash,
} from "@tabler/icons-react";
import Link from "next/link";
import { isJobRunRunning, statusTextStyle } from "src/utils";
import { GatherResponse } from "src/interfaces/gather";
import { jobRunService } from "src/services";
import { useRouter } from "next/navigation";
import { useGetLocale } from "@refinedev/core";

interface GatherRowProps {
	row: GatherResponse;
	setSelected: React.Dispatch<React.SetStateAction<any>>;
	setDeleteModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
	translate: (key: string) => string;
}

const GatherRow: React.FC<GatherRowProps> = ({
	row,
	setSelected,
	setDeleteModalOpen,
	translate,
}) => {
	const router = useRouter();
	const locale = useGetLocale();
	const currentLocale = locale();
	const { id, name, child_type, project_id } = row;

	// Initialize local state with data from props
	const [latestJobRun, setLatestJobRun] = useState(row.latest_job_run);
	const [deleteJobRun, setDeleteJobRun] = useState(row.delete_job_run);
	const [isLoading, setIsLoading] = useState(false);

	// Update local state when props change
	useEffect(() => {
		setLatestJobRun(row.latest_job_run);
		setDeleteJobRun(row.delete_job_run);
	}, [row.latest_job_run, row.delete_job_run]);

	// Function to refresh the gather data
	// !!! IMPORTANT THIS NEEDS TO BE REFACTORED TO WORK
	const handleGatherRefresh = useCallback(async () => {
		setIsLoading(true);
		if (project_id) {
			try {
				const latestJobRunFetch = await jobRunService.fetchJobRun({
					project_id: Number(project_id),
					id: latestJobRun?.id,
				});
				let deleteJobRunFetch = { data: null };
				if (deleteJobRun?.id) {
					deleteJobRunFetch = await jobRunService.fetchJobRun({
						project_id: Number(project_id),
						id: deleteJobRun.id,
					});
				}

				// Update local state
				setLatestJobRun(latestJobRunFetch.data);
				if (deleteJobRunFetch.data) setDeleteJobRun(deleteJobRunFetch.data);
			} catch (error) {
				console.error("Error fetching gather details:", error);
			} finally {
				setIsLoading(false);
			}
		}
	}, [project_id, latestJobRun?.id, deleteJobRun?.id]);

	// Use effect to refresh pending gathers at intervals
	useEffect(() => {
		let interval: NodeJS.Timeout | undefined;
		const isPending =
			(latestJobRun && !latestJobRun.completed_at) ||
			(deleteJobRun && !deleteJobRun.completed_at);

		if (isPending) {
			interval = setInterval(() => {
				handleGatherRefresh();
			}, 10000);
		}
		return () => {
			if (interval) {
				clearInterval(interval);
			}
		};
	}, [latestJobRun, deleteJobRun, handleGatherRefresh]);

	const status = latestJobRun ? latestJobRun.status : null;

	return (
		<tr>
			<td>
				<Link
					href={`/projects/${project_id}/gathers/${child_type}/${id}`}
					className="no-underline text-blue-500"
				>
					{name}
				</Link>
			</td>
			<td>
				{latestJobRun?.completed_at ? (
					<span
						className={`${
							deleteJobRun?.status === "completed_successfully"
								? statusTextStyle("deleted")
								: ""
						}`}
					>
						<DateField
							format="LLL"
							value={latestJobRun.completed_at}
							locales={currentLocale}
						/>
					</span>
				) : (
					""
				)}
			</td>
			<td>
				<div className="text-center flex items-center">
					{latestJobRun?.completed_at && latestJobRun?.total_cost !== null ? (
						<Text>{latestJobRun.total_cost.toFixed(2)}</Text>
					) : (
						""
					)}
					{latestJobRun?.is_total_cost_estimated && (
						<Tooltip
							multiline
							width={350}
							label={translate("gathers.cautions.is_total_cost_estimated")}
						>
							<Button p={0} variant="subtle" color="orange">
								<IconAlertTriangle size={20} color="orange" />
							</Button>
						</Tooltip>
					)}
				</div>
			</td>
			<td>
				{latestJobRun?.completed_at && latestJobRun?.gather_result_count ? (
					<Text>
						{["danek_instagram_posts", "danek_instagram_comments"].includes(
							child_type
						)
							? "~" + latestJobRun.gather_result_count * 10
							: latestJobRun.gather_result_count}
					</Text>
				) : (
					""
				)}
			</td>
			<td>
				{latestJobRun?.completed_at &&
				latestJobRun?.gather_normalise_error_count ? (
					<Text>{latestJobRun.gather_normalise_error_count}</Text>
				) : (
					""
				)}
			</td>
			<td>
				<span
					className={`${statusTextStyle(
						deleteJobRun?.status === "completed_successfully"
							? "deleted"
							: deleteJobRun?.status
								? deleteJobRun?.status
								: status
					)}`}
				>
					{deleteJobRun
						? translate(`status.delete_status.${deleteJobRun.status}`)
						: status
							? translate(`status.${status}`)
							: ""}
				</span>
			</td>
			<td>
				<Group spacing="xs" noWrap>
					{isLoading ? (
						<Loader size="sm" />
					) : (
						<>
							{!status && (
								<Tooltip
									label={translate("gathers.actions.titles.view_and_run")}
								>
									<Button
										p={0}
										variant="subtle"
										color="green"
										onClick={() => {
											setSelected(row);
											router.push(
												`/projects/${project_id}/gathers/${child_type}/${id}`
											);
										}}
									>
										<IconPlayerPlay size={20} color="green" />
									</Button>
								</Tooltip>
							)}
							{(isJobRunRunning(latestJobRun) ||
								isJobRunRunning(deleteJobRun)) && <Loader size="sm" />}
							{latestJobRun?.completed_at &&
								!isJobRunRunning(deleteJobRun) &&
								deleteJobRun?.status !== "completed_successfully" && (
									<Tooltip label="Delete">
										<Button
											p={0}
											variant="subtle"
											color="red"
											onClick={() => {
												setSelected(row);
												setDeleteModalOpen(true);
											}}
										>
											<IconTrash size={20} color="red" />
										</Button>
									</Tooltip>
								)}
						</>
					)}
				</Group>
			</td>
		</tr>
	);
};

export default GatherRow;
