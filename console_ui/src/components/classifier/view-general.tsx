"use client";

import { Anchor, Container, Group, Title } from "@mantine/core";
import { useGetLocale, useTranslate } from "@refinedev/core";
import { DateField, TextField } from "@refinedev/mantine";
import React from "react";

interface Props {
	record: any;
}

const ClassifierViewGeneral: React.FC<Props> = ({ record }) => {
	const translate = useTranslate();
	const locale = useGetLocale();
	const currentLocale = locale();
	return (
		<Container className="mx-0 flex flex-col my-4">
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.name")}:
				</Title>
				<TextField className="capitalize" value={record?.name} />
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("projects.fields.description")}:
				</Title>
				<TextField className="capitalize" value={record?.description} />
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("gathers.fields.created_at")}:
				</Title>
				{record?.created_at ? (
					<DateField
						format="LLL"
						value={record?.created_at}
						locales={currentLocale}
					/>
				) : (
					"-"
				)}
			</Group>
			<Group>
				<Title my="xs" order={5}>
					{translate("classifiers.fields.latest_version_applyed_at")}:
				</Title>
				{record?.latest_version?.created_at ? (
					<DateField
						format="LLL"
						value={record?.latest_version?.created_at}
						locales={currentLocale}
					/>
				) : (
					"-"
				)}
			</Group>
			{record?.type !== "hugging_face" && (
				<Group>
					<Title my="xs" order={5}>
						{translate("classifiers.fields.latest_edits_made_at")}:
					</Title>
					{record?.last_edited_at ? (
						<DateField
							format="LLL"
							value={record?.last_edited_at}
							locales={currentLocale}
						/>
					) : (
						"-"
					)}
				</Group>
			)}
			{record?.type === "hugging_face" && (
				<Group>
					<Title my="xs" order={5}>
						{translate("classifiers.types.hugging_face.input.model")}:
					</Title>
					{record?.latest_version?.params?.model_id ? (
						<Anchor
							className="font-normal text-inherit !text-blue-500 text-sm underline"
							href={`https://huggingface.co/${record.latest_version.params.model_id}`}
							target="_blank"
						>
							{record?.latest_version?.params?.model_id}
						</Anchor>
					) : (
						"-"
					)}
				</Group>
			)}
		</Container>
	);
};

export default ClassifierViewGeneral;
