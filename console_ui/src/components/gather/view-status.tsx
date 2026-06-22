import { Button, Container, Group, Title, Tooltip } from "@mantine/core";
import { IconAlertTriangle, IconInfoCircle } from "@tabler/icons-react";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { DateField, TextField } from "@refinedev/mantine";
import React from "react";
import { formatNumber, statusTextStyle } from "src/utils";

interface Props {
	record: any;
}

const GatherViewStatus: React.FC<Props> = ({ record }) => {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	return (
		<Container className="mx-0 flex flex-col my-4">
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.latest_job_id")}:
				</Title>
				{record?.latest_job_run?.id}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.status")}:
				</Title>
				<span className={`${statusTextStyle(record?.latest_job_run?.status)}`}>
					{record?.latest_job_run?.status
						? translate(`status.${record.latest_job_run.status}`)
						: "-"}
				</span>
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.started_processing_at")}:
				</Title>
				{record?.latest_job_run?.started_processing_at ? (
					<DateField
						format="LLL"
						value={record?.latest_job_run.started_processing_at}
						locales={currentLocale}
					/>
				) : (
					"-"
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.completed_at")}:
				</Title>
				{record?.latest_job_run?.completed_at ? (
					<DateField
						format="LLL"
						value={record?.latest_job_run.completed_at}
						locales={currentLocale}
					/>
				) : (
					"-"
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("buttons.delete")} {translate("projects.fields.status")}:
				</Title>
				{record?.delete_job_run ? (
					<TextField
						className={`capitalize ${statusTextStyle(record?.delete_job_run?.status === "completed_successfully" ? "deleted" : record?.delete_job_run?.status)}`}
						value={translate(
							`status.delete_status.${record.delete_job_run.status}`
						)}
					/>
				) : (
					"-"
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.total_cost")}:
				</Title>
				{record?.latest_job_run?.total_cost
					? formatNumber(record.latest_job_run.total_cost)
					: "-"}{" "}
				{record?.latest_job_run?.is_total_cost_estimated && (
					<Tooltip
						multiline
						width={350}
						label={translate("gathers.cautions.is_total_cost_estimated")}
					>
						<Button p={0} variant="subtle" color="orange">
							<IconAlertTriangle
								size={20}
								color="orange"
								className="cursor-pointer"
							/>
						</Button>
					</Tooltip>
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					<Tooltip
						label={translate("gathers.fields.result_count_tooltip")}
						width={200}
						multiline
					>
						<span>
							<IconInfoCircle size={14} />
						</span>
					</Tooltip>
					&nbsp;
					{translate("gathers.fields.result_count")}:
				</Title>
				{record?.latest_job_run?.gather_result_count
					? ["danek_instagram_posts", "danek_instagram_comments"].includes(
							record.child_type
						)
						? "~" + record.latest_job_run.gather_result_count * 10
						: record.latest_job_run.gather_result_count
					: "-"}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					<Tooltip
						label={translate("gathers.fields.error_count_tooltip")}
						width={200}
						multiline
					>
						<span>
							<IconInfoCircle size={14} />
						</span>
					</Tooltip>
					&nbsp;
					{translate("gathers.fields.error_count")}:
				</Title>
				{record?.latest_job_run?.gather_normalise_error_count
					? record.latest_job_run.gather_normalise_error_count
					: "-"}
			</Group>
		</Container>
	);
};

export default GatherViewStatus;
