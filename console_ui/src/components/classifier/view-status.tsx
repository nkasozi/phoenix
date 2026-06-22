"use client";

import { Container, Group, Title } from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { DateField } from "@refinedev/mantine";
import React from "react";
import { statusTextStyle } from "src/utils";

interface Props {
	record: any;
}

const ClassifierViewStatus: React.FC<Props> = ({ record }) => {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	return (
		<Container className="mx-0 flex flex-col my-4">
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
			</Group>{" "}
		</Container>
	);
};

export default ClassifierViewStatus;
