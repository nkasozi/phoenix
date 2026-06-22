"use client";

import React from "react";
import {
	TextInput,
	NumberInput,
	Select,
	Textarea,
	Alert,
	Tooltip,
	Checkbox,
} from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import { IconInfoCircle } from "@tabler/icons-react";
import { GetInputProps } from "@mantine/form/lib/types";
import { ProjectSchema } from "src/interfaces/project";

const PROJECT_NAME_INVALID_CHARS_REGEX = new RegExp(
	"[^\\p{L}\\p{N}\\s_-]",
	"gu"
);
const PROJECT_NAME_WHITESPACE_REGEX = /\s+/g;

function isValidProjectName(name: string) {
	const normalizedName = name
		.replace(PROJECT_NAME_WHITESPACE_REGEX, " ")
		.trim();
	const sanitizedName = name
		.replace(PROJECT_NAME_INVALID_CHARS_REGEX, "")
		.replace(PROJECT_NAME_WHITESPACE_REGEX, " ")
		.trim();

	return normalizedName.length > 0 && sanitizedName === normalizedName;
}

interface Props {
	state?: string;
	getInputProps: GetInputProps<ProjectSchema>;
}

export const initialFormValues = {
	name: "",
	description: "",
	workspace_slug: "",
	// 180 is the standard value for projects is the BU data policy
	pi_deleted_after_days: 180,
	delete_after_days: 180,
	expected_usage: "",
	has_unlimited_credits: false,
	dashboard_id: undefined,
};

export function getProjectValidationRules(
	data: any,
	translate: any,
	state = "create"
) {
	const validationRules: any = {};

	validationRules.name =
		data.name.trim().length <= 0
			? translate("projects.fields.validation.required")
			: !isValidProjectName(data.name)
				? translate("projects.fields.validation.invalid_name")
				: null;
	validationRules.workspace_slug =
		data.workspace_slug.length <= 0
			? translate("projects.fields.validation.required")
			: null;
	validationRules.expected_usage =
		data.expected_usage.length <= 0
			? translate("projects.fields.validation.required")
			: null;
	validationRules.pi_deleted_after_days =
		data.pi_deleted_after_days === undefined
			? translate("projects.fields.validation.required")
			: null;
	validationRules.delete_after_days =
		data.delete_after_days === undefined
			? translate("projects.fields.validation.required")
			: null;

	if (data.pi_deleted_after_days < 30 || data.pi_deleted_after_days > 365) {
		validationRules.pi_deleted_after_days = translate(
			"projects.fields.validation.days_until_pi_expiration"
		);
	}
	if (data.delete_after_days < 30 || data.delete_after_days > 365) {
		validationRules.delete_after_days = translate(
			"projects.fields.validation.days_until_all_data_expiration"
		);
	}
	if (!data.has_unlimited_credits && state === "create") {
		validationRules.initial_credit_allocation_amount =
			data.initial_credit_allocation_amount === undefined
				? translate("projects.fields.validation.required")
				: null;
		validationRules.initial_credit_allocation_description =
			data.initial_credit_allocation_description === undefined ||
			data.initial_credit_allocation_description.length <= 0
				? translate("projects.fields.validation.required")
				: null;
	}

	return validationRules;
}

const CreateEditProjectForm: React.FC<Props> = ({
	state = "create",
	getInputProps,
}) => {
	const translate = useTranslate();
	return (
		<>
			<TextInput
				mt="sm"
				label={translate("projects.fields.name")}
				{...getInputProps("name")}
			/>
			<Select
				mt="sm"
				label={translate("projects.fields.workspace_slug")}
				{...getInputProps("workspace_slug")}
				data={[
					{ label: translate("inputs.select"), value: "" },
					{ label: "Main", value: "main" },
				]}
			/>
			<NumberInput
				mt="sm"
				min={30}
				max={365}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate("projects.warnings.days_until_pi_expiration")}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("projects.fields.days_until_pi_expiration")}
					</div>
				}
				{...getInputProps("pi_deleted_after_days")}
			/>
			<NumberInput
				mt="sm"
				min={30}
				max={365}
				label={
					<div className="flex items-center">
						<Tooltip
							label={translate(
								"projects.warnings.days_until_all_data_expiration"
							)}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("projects.fields.days_until_all_data_expiration")}
					</div>
				}
				{...getInputProps("delete_after_days")}
			/>
			<Select
				mt="sm"
				label={translate("projects.fields.expected_usage.title")}
				data={[
					{ label: translate("inputs.select"), value: "" },
					{
						label: translate("projects.fields.expected_usage.options.one_off"),
						value: "one_off",
					},
					{
						label: translate("projects.fields.expected_usage.options.monthly"),
						value: "monthly",
					},
					{
						label: translate("projects.fields.expected_usage.options.weekly"),
						value: "weekly",
					},
					{
						label: translate("projects.fields.expected_usage.options.daily"),
						value: "daily",
					},
				]}
				{...getInputProps("expected_usage")}
			/>
			<Textarea
				mt="sm"
				label={translate("projects.fields.inputs.description")}
				{...getInputProps("description")}
			/>
			<Checkbox
				mt="md"
				label={translate("projects.fields.has_unlimited_credits")}
				{...getInputProps("has_unlimited_credits", { type: "checkbox" })}
			/>
			{state === "create" &&
				getInputProps("has_unlimited_credits").value !== true && (
					<>
						<NumberInput
							mt="sm"
							min={0}
							label={translate(
								"projects.fields.initial_credit_allocation_amount"
							)}
							disabled={getInputProps("has_unlimited_credits").value === true}
							{...getInputProps("initial_credit_allocation_amount")}
						/>
						<Textarea
							mt="sm"
							label={translate(
								"projects.fields.initial_credit_allocation_description"
							)}
							disabled={getInputProps("has_unlimited_credits").value === true}
							{...getInputProps("initial_credit_allocation_description")}
						/>
					</>
				)}
			<NumberInput
				mt="sm"
				min={1}
				label={
					<div className="flex items-center">
						<Tooltip
							width={300}
							multiline
							label={translate("projects.fields.dashboard_id_tooltip")}
						>
							<span className="flex">
								<IconInfoCircle size={12} />
							</span>
						</Tooltip>
						{translate("projects.fields.dashboard_id")}
					</div>
				}
				{...getInputProps("dashboard_id")}
			/>
			<Alert mt="lg" title={translate("note")} color="gray">
				{translate("projects.warnings.create")}
			</Alert>
		</>
	);
};

export default CreateEditProjectForm;
