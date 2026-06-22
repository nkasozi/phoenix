import GatherRunModal from "@components/modals/gather-run";
import { Button, Container, Group, Title, Tooltip } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { useTranslate } from "@refinedev/core";
import React, { useState } from "react";
import {
	formatMaxCreditAfterRun,
	formatNumber,
	gatherJobRunEstimateToBig,
	gatherJobRunEstimateToBigWithRunningJobs,
	projectHasRemainingCredits,
} from "src/utils";
import GatherRunChecks from "./gather-run-check";

interface Props {
	record: any;
	refetch: any;
	projectInfo: any;
}

const GatherViewRun: React.FC<Props> = ({ record, refetch, projectInfo }) => {
	const translate = useTranslate();
	const [opened, setOpened] = useState(false);
	return (
		<Container className="mx-0 flex flex-col my-4">
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.run_estimate.max_no_results")}:
				</Title>
				<span>
					{record?.job_run_resource_estimate?.max_gather_result_count
						? formatNumber(
								record.job_run_resource_estimate.max_gather_result_count
							)
						: "?"}
				</span>
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.run_estimate.max_credit_for_run")}:
				</Title>
				{record?.job_run_resource_estimate?.max_gather_result_count
					? formatNumber(record.job_run_resource_estimate.max_total_cost)
					: "?"}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					<Tooltip
						label={translate(
							"gathers.run_estimate.max_credit_after_run_tooltip"
						)}
						width={200}
						multiline
					>
						<span>
							<IconInfoCircle size={14} />
						</span>
					</Tooltip>
					&nbsp;
					{translate("gathers.run_estimate.max_credit_after_run")}:
				</Title>
				{formatMaxCreditAfterRun(projectInfo, record)}
			</Group>
			<GatherRunChecks projectInfo={projectInfo} gatherDetail={record} />
			<Group>
				<Button
					onClick={() => setOpened(true)}
					disabled={
						record?.latest_job_run ||
						gatherJobRunEstimateToBig(projectInfo, record) ||
						!projectHasRemainingCredits(projectInfo) ||
						gatherJobRunEstimateToBigWithRunningJobs(projectInfo, record)
					}
				>
					{translate("gathers.actions.titles.run")}
				</Button>
			</Group>
			<GatherRunModal
				opened={opened}
				setOpened={setOpened}
				gatherDetail={record}
				projectInfo={projectInfo}
				refetch={refetch}
			/>
		</Container>
	);
};

export default GatherViewRun;
