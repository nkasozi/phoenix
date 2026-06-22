"use client";

import React, { useState } from "react";
import {
	Anchor,
	FileInput,
	Space,
	Text,
	TextInput,
	Tooltip,
} from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle, IconUpload } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";
import { TextField } from "@refinedev/mantine";
import { MAX_MANUAL_UPLOAD_FILE_SIZE } from "src/utils";

export const initialFormValues = {
	name: "",
	file: null,
};

const DOC_LINK =
	"https://www.notion.so/howtobuildup/Manual-Upload-for-Social-Media-Data-16f45657183e808bb339ed5f0590860f";

// Define separate validation rules for posts
export function getManualUploadValidationRules(data: any, translate: any) {
	const validationRules: any = {};

	validationRules.name =
		data.name.length <= 0
			? translate("gathers.types.manual_upload.fields.validation.required")
			: null;

	validationRules.file =
		data.file === undefined || !data.file
			? translate("gathers.types.manual_upload.fields.validation.required")
			: null;

	return validationRules;
}

interface Props {
	getInputProps: GetInputProps<ProjectSchema>;
	file: File | null;
	setFile: any;
}

const ManualUploadForm: React.FC<Props> = ({
	getInputProps,
	file,
	setFile,
}) => {
	const translate = useTranslate();
	const [fileError, setFileError] = useState("");

	// File validation function
	const validateFile = (input: File | null) => {
		if (!input) return;

		// Check file type (CSV)
		if (input.type !== "text/csv") {
			setFileError(
				translate(
					"gathers.types.manual_upload.fields.validation.invalid_file_type"
				)
			);
			setFile(null); // Clear the file input
			return;
		}

		// Check file size (max 1GB)
		if (input.size > MAX_MANUAL_UPLOAD_FILE_SIZE) {
			setFileError(
				translate(
					"gathers.types.manual_upload.fields.validation.file_too_large"
				)
			);
			setFile(null);
			return;
		}
		setFileError("");
	};

	return (
		<>
			<TextField
				value={translate(
					"gathers.types.manual_upload.create_description.part1"
				)}
			/>
			<Space h="sm" />
			<Text>
				{translate("gathers.types.manual_upload.create_description.part2.a")}{" "}
				<Anchor
					className="font-normal hover:text-blue-500 text-sm underline"
					href={DOC_LINK}
					target="_blank"
				>
					{translate("gathers.types.manual_upload.create_description.part2.b")}
				</Anchor>
				.
			</Text>
			<Space h="sm" />
			<TextField
				value={translate(
					"gathers.types.manual_upload.create_description.part3"
				)}
			/>
			<Space h="lg" />
			<TextInput
				mt="sm"
				label={
					<div className="flex items-center">
						<Tooltip label={translate("gathers.fields.info.name")}>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("gathers.types.manual_upload.fields.name")}
					</div>
				}
				{...getInputProps("name")}
			/>
			<FileInput
				mt="sm"
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate("gathers.types.manual_upload.fields.info.file")}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("gathers.types.manual_upload.fields.file")}
					</div>
				}
				{...getInputProps("file")}
				value={file}
				onChange={(input: File | null) => {
					getInputProps("file").onChange(input);
					setFile(input);
					validateFile(input); // Call file validation
				}}
				error={
					getInputProps("file").error ? getInputProps("file").error : fileError
				}
				accept=".csv" // Only accept CSV files
				icon={<IconUpload size={14} />}
			/>
		</>
	);
};

export default ManualUploadForm;
