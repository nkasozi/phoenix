"use client";

import { Text } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import React from "react";
import {
	gatherJobRunEstimateToBig,
	gatherJobRunEstimateToBigWithRunningJobs,
	projectHasRemainingCredits,
} from "src/utils";

interface Props {
	gatherDetail: any;
	projectInfo: any;
}

const GatherRunChecks: React.FC<Props> = ({ gatherDetail, projectInfo }) => {
	const translate = useTranslate();
	let message: string | null = null;

	if (!projectHasRemainingCredits(projectInfo)) {
		message = translate("gathers.caution.no_credit");
	} else if (gatherJobRunEstimateToBig(projectInfo, gatherDetail)) {
		message = translate("gathers.caution.over_cost");
	} else if (
		gatherJobRunEstimateToBigWithRunningJobs(projectInfo, gatherDetail)
	) {
		message = translate("gathers.caution.pending_cost");
	}

	return (
		<div className="w-full flex flex-col gap-2 my-5">
			{message && (
				<Text className="text-base text-red-500 font-normal">{message}</Text>
			)}
		</div>
	);
};

export default GatherRunChecks;
