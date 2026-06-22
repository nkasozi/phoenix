"use client";

import { TextInput, Tooltip, ActionIcon, Checkbox } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";

interface AddKeywordRowProps {
	classKey: number;
	classClientId: string;
	mustsValue: string;
	isRegexValue: boolean;
	translate: (key: string) => string;
	onMustsChange: (classKey: number, value: string) => void;
	onIsRegexChange: (classKey: number, checked: boolean) => void;
	onAdd: (classKey: number) => void;
	onShowRow: (key: string) => void;
}

const AddKeywordRow: React.FC<AddKeywordRowProps> = ({
	classKey,
	classClientId,
	mustsValue,
	isRegexValue,
	translate,
	onMustsChange,
	onIsRegexChange,
	onAdd,
	onShowRow,
}) => {
	const hasUnsavedInput = !!mustsValue.trim();

	return (
		<tr className={hasUnsavedInput ? "bg-orange-50" : "bg-blue-50"}>
			<td>
				<TextInput
					placeholder={translate("classifiers.actions.tooltips.add_keyword")}
					size="xs"
					value={mustsValue}
					onChange={(e) => onMustsChange(classKey, e.target.value)}
					onKeyDown={(e) => {
						if (e.key === "Enter") {
							onShowRow(classClientId);
							onAdd(classKey);
						}
					}}
				/>
				{hasUnsavedInput && (
					<div className="text-xs text-orange-500 mt-1">
						{translate("classifiers.info.unsaved_keyword")}
					</div>
				)}
			</td>
			<td>
				<Checkbox
					size="xs"
					checked={isRegexValue}
					onChange={(e) => onIsRegexChange(classKey, e.target.checked)}
				/>
			</td>
			<td>
				<Tooltip label={translate("classifiers.actions.tooltips.add_keyword")}>
					<ActionIcon
						color="blue"
						variant="light"
						onClick={() => {
							onShowRow(classClientId);
							onAdd(classKey);
						}}
					>
						<IconPlus size={16} />
					</ActionIcon>
				</Tooltip>
			</td>
		</tr>
	);
};

export default AddKeywordRow;
