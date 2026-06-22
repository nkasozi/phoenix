"use client";

import GatherRunChecks from "@components/gather/gather-run-check";
import { Modal, Button, Text, Tooltip } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { useGo, useTranslate } from "@refinedev/core";
import { useState } from "react";
import { gatherService } from "src/services";
import {
	formatMaxCreditAfterRun,
	formatNumber,
	gatherJobRunEstimateToBig,
	gatherJobRunEstimateToBigWithRunningJobs,
	normaliseErrorMessage,
	projectHasRemainingCredits,
} from "src/utils";

interface Props {
	opened: boolean;
	setOpened: any;
	gatherDetail: any;
	projectInfo: any;
	refetch: any;
}

const GatherRunModal: React.FC<Props> = ({
	opened,
	setOpened,
	gatherDetail,
	projectInfo,
	refetch,
}) => {
	const go = useGo();
	const translate = useTranslate();
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const handleClose = () => {
		setOpened(false);
		setError(null);
	};

	const handleStartRun = () => {
		setLoading(true);
		setError("");
		gatherService
			.run({
				project_id: gatherDetail.project_id,
				id: gatherDetail.id,
			})
			.then(() => {
				refetch();
				handleClose();
				go({
					to: `/projects/show/${projectInfo?.id}?activeItem=gather`,
					type: "push",
				});
				setLoading(false);
			})
			.catch((err) => {
				setError(normaliseErrorMessage(err, translate));
				setLoading(false);
			});
	};
	return (
		<Modal
			opened={opened}
			size="lg"
			onClose={() => setOpened(false)}
			withCloseButton={false}
		>
			<div className="font-medium flex flex-col px-8 pb-8">
				<h3 className="flex w-full items-center mb-6">
					<span className="font-medium text-xl">
						{translate("gathers.run_estimate.title")}
					</span>
				</h3>
				{error && <span className="text-red-500">{error}</span>}
				<div>
					<div className="w-full flex flex-col mb-5 p-1">
						<Text className="text-base text-neutral-500 font-normal">
							{translate("gathers.fields.name")}
						</Text>
						<Text className="font-medium text-lg capitalize">
							{gatherDetail?.name}
						</Text>
					</div>
					{gatherDetail?.description && (
						<div className="w-full flex flex-col mb-5 p-1">
							<Text className="text-base text-neutral-500 font-normal">
								{translate("projects.fields.description")}
							</Text>
							<Text className="font-medium text-lg capitalize">
								{gatherDetail?.description}
							</Text>
						</div>
					)}
					<div className="mb-4">
						<Text className="mb-4 uppercase font-medium text-base text-neutral-600 tracking-widest">
							{translate("gathers.run_estimate.cost")}:
						</Text>
					</div>
					<div className="w-full flex gap-2 mb-5 p-1">
						<Text className="text-base text-neutral-500 font-normal">
							{translate("gathers.run_estimate.max_no_results")}:
						</Text>
						<Text className="font-medium text text-">
							{gatherDetail?.job_run_resource_estimate?.max_gather_result_count
								? formatNumber(
										gatherDetail.job_run_resource_estimate
											.max_gather_result_count
									)
								: "?"}
						</Text>
					</div>

					<div className="w-full flex gap-2 mb-5 p-1">
						<Text className="text-base text-neutral-500 font-normal">
							{translate("gathers.run_estimate.max_credit_for_run")}:
						</Text>
						<Text className="font-medium text text-">
							{gatherDetail?.job_run_resource_estimate?.max_gather_result_count
								? formatNumber(
										gatherDetail.job_run_resource_estimate.max_total_cost
									)
								: "?"}
						</Text>
					</div>

					<div className="w-full flex gap-2 mb-5 p-1">
						<Text className="text-base text-neutral-500 font-normal">
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
						</Text>
						<Text className="font-medium text text-">
							{formatMaxCreditAfterRun(projectInfo, gatherDetail)}
						</Text>
					</div>
					<GatherRunChecks
						projectInfo={projectInfo}
						gatherDetail={gatherDetail}
					/>
				</div>
				<div className="flex justify-end items-center mt-4">
					<div className="flex gap-4" role="group">
						<Button variant="subtle" color="red" onClick={handleClose}>
							{translate("buttons.cancel")}
						</Button>
						<Button
							onClick={handleStartRun}
							loading={loading}
							disabled={
								loading ||
								gatherJobRunEstimateToBig(projectInfo, gatherDetail) ||
								!projectHasRemainingCredits(projectInfo) ||
								gatherJobRunEstimateToBigWithRunningJobs(
									projectInfo,
									gatherDetail
								)
							}
						>
							{translate("buttons.start_run")}
						</Button>
					</div>
				</div>
			</div>
		</Modal>
	);
};

export default GatherRunModal;
