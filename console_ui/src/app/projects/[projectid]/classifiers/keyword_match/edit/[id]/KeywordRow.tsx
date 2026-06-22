"use client";

import {
	TextInput,
	Tooltip,
	ActionIcon,
	Checkbox,
	Loader,
} from "@mantine/core";
import { IconTrash, IconCheck, IconExclamationMark } from "@tabler/icons-react";
import { ChangeEvent } from "react";
import type { SaveStatus } from "./useSaveStatus";

interface KeywordGroup {
	id?: number;
	clientId: string;
	class_id: number;
	musts: string;
	nots?: string;
	is_regex?: boolean;
	class_name?: string;
}

interface KeywordRowProps {
	keywordGroup: KeywordGroup;
	saveStatus?: SaveStatus;
	translate: (key: string) => string;
	onKeywordChange: (clientId: string, value: string) => void;
	onKeywordSave: (clientId: string) => void;
	onRegexToggle: (clientId: string, checked: boolean) => void;
	onRemove: (clientId: string) => void;
	onModified: () => void;
}

const SaveStatusIndicator: React.FC<{
	status?: SaveStatus;
	onRetry?: () => void;
}> = ({ status, onRetry }) => {
	if (!status) return null;
	if (status === "saving") {
		return (
			<span className="inline-flex items-center text-xs text-gray-500 ml-2">
				<Loader size={12} className="mr-1" />
				Saving...
			</span>
		);
	}
	if (status === "saved") {
		return (
			<span className="inline-flex items-center text-xs text-green-600 ml-2">
				<IconCheck size={12} className="mr-1" />
				Saved
			</span>
		);
	}
	if (status === "error") {
		return (
			<span className="inline-flex items-center text-xs text-red-600 ml-2">
				<IconExclamationMark size={12} className="mr-1" />
				Error
				{onRetry && (
					<button
						className="ml-1 underline text-red-600 hover:text-red-800"
						onClick={onRetry}
					>
						Retry
					</button>
				)}
			</span>
		);
	}
	return null;
};

const KeywordRow: React.FC<KeywordRowProps> = ({
	keywordGroup,
	saveStatus,
	translate,
	onKeywordChange,
	onKeywordSave,
	onRegexToggle,
	onRemove,
	onModified,
}) => {
	return (
		<tr>
			<td>
				<div className="flex items-center">
					<TextInput
						placeholder={translate("classifiers.fields.keywords_placeholder")}
						value={keywordGroup.musts}
						onChange={(event: ChangeEvent<HTMLInputElement>) => {
							onKeywordChange(keywordGroup.clientId, event.target.value);
							onModified();
						}}
						onBlur={() => {
							onKeywordSave(keywordGroup.clientId);
						}}
						className="flex-1"
					/>
					<SaveStatusIndicator
						status={saveStatus}
						onRetry={
							saveStatus === "error"
								? () => onKeywordSave(keywordGroup.clientId)
								: undefined
						}
					/>
				</div>
			</td>
			<td>
				<Checkbox
					size="xs"
					checked={keywordGroup.is_regex || false}
					onChange={(e) =>
						onRegexToggle(keywordGroup.clientId, e.target.checked)
					}
				/>
			</td>
			<td>
				<Tooltip
					label={translate("classifiers.actions.tooltips.delete_keyword")}
				>
					<ActionIcon
						color="red"
						variant="light"
						onClick={() => onRemove(keywordGroup.clientId)}
					>
						<IconTrash size={16} />
					</ActionIcon>
				</Tooltip>
			</td>
		</tr>
	);
};

export default KeywordRow;
