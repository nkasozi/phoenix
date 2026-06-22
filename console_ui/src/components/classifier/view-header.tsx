"use client";

import { useTranslate } from "@refinedev/core";
import React, { Dispatch, SetStateAction } from "react";
import { EditButton, EditButtonProps, TextField } from "@refinedev/mantine";
import { Button, Text, Tooltip } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";

interface Props {
	id: string;
	record: any;
	setOpened: Dispatch<SetStateAction<boolean>>;
}

const ClassifierViewHeader: React.FC<Props> = ({ id, record, setOpened }) => {
	const translate = useTranslate();
	const editButtonProps: EditButtonProps = {
		recordItemId: id as string,
	};
	return (
		<div className="w-full flex flex-col gap-2">
			<TextField
				className="mb-2"
				value={translate(`classifiers.types.${record?.type}.view.text`)}
			/>
			{!record?.latest_version && (
				<Text className="flex items-center text-red-500">
					{translate("classifiers.cautions.not_run.title")}
					<Tooltip
						multiline
						width={350}
						label={translate("classifiers.cautions.not_run.description")}
					>
						<span className="flex">
							<IconInfoCircle size={12} />
						</span>
					</Tooltip>
				</Text>
			)}
			{record?.latest_version &&
				new Date(record?.latest_version?.created_at) <
					new Date(record?.last_edited_at) && (
					<Text className="flex items-center text-red-500">
						{translate("classifiers.cautions.not_applied.title")}
						<Tooltip
							multiline
							width={350}
							label={translate("classifiers.cautions.not_applied.description")}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
					</Text>
				)}
			{record?.type === "manual_post_authors" &&
				record?.intermediatory_author_classes?.length < 1 && (
					<Text className="flex items-center text-red-500">
						{translate("classifiers.cautions.no_author_class")}
					</Text>
				)}
			{record?.type === "keyword_match" &&
				record?.intermediatory_class_to_keyword_configs?.length < 1 && (
					<Text className="flex items-center text-red-500">
						{translate("classifiers.cautions.no_keyword_configurations")}
					</Text>
				)}
			{(record?.type === "manual_post_authors" ||
				record?.type === "keyword_match") && (
				<div className="flex gap-4 items-center my-4">
					<EditButton {...editButtonProps} />
					<Button
						variant="filled"
						color="blue"
						onClick={() => setOpened(true)}
						disabled={
							(record?.type === "manual_post_authors" &&
								record?.intermediatory_author_classes?.length < 1) ||
							(record?.type === "keyword_match" &&
								record?.intermediatory_class_to_keyword_configs?.length < 1) ||
							(!record?.latest_version && !record?.last_edited_at) ||
							(record?.latest_job_run &&
								!record?.latest_job_run?.completed_at) ||
							(record?.latest_version &&
								new Date(record?.latest_version?.created_at) >
									new Date(record?.last_edited_at))
						}
					>
						{translate("classifiers.run")}
					</Button>
				</div>
			)}
			{record?.type === "perspective_api" && (
				<div className="flex gap-4 items-center my-4">
					<EditButton color="blue" variant="outline" {...editButtonProps}>
						{translate("classifiers.types.perspective_api.view.edit_run")}
					</EditButton>
				</div>
			)}
		</div>
	);
};

export default ClassifierViewHeader;
