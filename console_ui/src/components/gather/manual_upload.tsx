"use client";

import { Text } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import React from "react";

interface Props {
	response: any;
}

const ManualUploadGatherChecks: React.FC<Props> = ({ response }) => {
	const translate = useTranslate();
	let message: string | null = null;

	if (response?.detail?.error_message_i18n_key === "column_not_in_dataframe") {
		message = translate(
			"gathers.types.manual_upload.errors.column_not_in_dataframe"
		);
	} else if (
		response?.detail?.error_message_i18n_key === "column_not_in_schema"
	) {
		message = translate(
			"gathers.types.manual_upload.errors.column_not_in_schema"
		);
	} else if (response?.detail?.error_message_i18n_key === "dataframe_check") {
		message = translate("gathers.types.manual_upload.errors.dataframe_check");
	}

	return (
		<div className="w-full flex flex-col gap-2 my-5">
			{response?.detail?.error_message && (
				<Text className="text-base text-red-500 font-normal">
					{translate("gathers.types.manual_upload.errors.message")}
				</Text>
			)}
			{message && (
				<Text className="text-base text-red-500 font-normal">{message}</Text>
			)}
			{response?.detail?.error_message && (
				<Text className="text-base text-red-500 font-normal">
					{response?.detail?.error_message}
				</Text>
			)}
		</div>
	);
};

export default ManualUploadGatherChecks;
