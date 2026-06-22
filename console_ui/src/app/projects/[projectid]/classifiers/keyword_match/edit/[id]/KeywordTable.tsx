"use client";

import { Table, Tooltip, Anchor } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";
import KeywordRow from "./KeywordRow";
import AddKeywordRow from "./AddKeywordRow";
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

interface KeywordTableProps {
	classClientId: string;
	classSaveStatus?: SaveStatus;
	classKey: number;
	keywordGroups: KeywordGroup[];
	newMustsValue: string;
	newIsRegexValue: boolean;
	translate: (key: string) => string;
	getSaveStatus: (id: string) => SaveStatus | undefined;
	onMustsChange: (classKey: number, value: string) => void;
	onIsRegexChange: (classKey: number, checked: boolean) => void;
	onAdd: (classKey: number) => void;
	onShowRow: (key: string) => void;
	onKeywordChange: (clientId: string, value: string) => void;
	onKeywordSave: (clientId: string) => void;
	onRegexToggle: (clientId: string, checked: boolean) => void;
	onRemove: (clientId: string) => void;
	onModified: () => void;
}

const KeywordTable: React.FC<KeywordTableProps> = ({
	classClientId,
	classKey,
	keywordGroups,
	newMustsValue,
	newIsRegexValue,
	translate,
	getSaveStatus,
	onMustsChange,
	onIsRegexChange,
	onAdd,
	onShowRow,
	onKeywordChange,
	onKeywordSave,
	onRegexToggle,
	onRemove,
	onModified,
}) => {
	return (
		<tr key={`${classClientId}-keywords`}>
			<td colSpan={4} className="!p-0 !pl-8 bg-gray-50">
				<Table style={{ tableLayout: "fixed" }}>
					<thead>
						<tr>
							<th style={{ width: "auto" }}>
								<div className="flex items-center">
									{translate("classifiers.fields.keywords")}
									<Tooltip
										width={350}
										multiline
										label={translate("classifiers.info.create_keywords")}
									>
										<span className="flex ml-1">
											<IconInfoCircle size={12} />
										</span>
									</Tooltip>
								</div>
							</th>
							<th style={{ width: "100px" }}>
								<div className="flex items-center">
									{translate("classifiers.fields.is_regex")}
									<Tooltip
										width={350}
										multiline
										label={
											<>
												{translate("classifiers.info.is_regex")}{" "}
												<Anchor
													href="https://regexr.com/"
													target="_blank"
													size="xs"
												>
													{translate("classifiers.info.is_regex_link")}
												</Anchor>
											</>
										}
									>
										<span className="flex ml-1">
											<IconInfoCircle size={12} />
										</span>
									</Tooltip>
								</div>
							</th>
							<th style={{ width: "80px" }}>{translate("table.actions")}</th>
						</tr>
					</thead>
					<tbody>
						{keywordGroups.map((keywordGroup) => (
							<KeywordRow
								key={keywordGroup.clientId}
								keywordGroup={keywordGroup}
								saveStatus={getSaveStatus(keywordGroup.clientId)}
								translate={translate}
								onKeywordChange={onKeywordChange}
								onKeywordSave={onKeywordSave}
								onRegexToggle={onRegexToggle}
								onRemove={onRemove}
								onModified={onModified}
							/>
						))}
						<AddKeywordRow
							classKey={classKey}
							classClientId={classClientId}
							mustsValue={newMustsValue}
							isRegexValue={newIsRegexValue}
							translate={translate}
							onMustsChange={onMustsChange}
							onIsRegexChange={onIsRegexChange}
							onAdd={onAdd}
							onShowRow={onShowRow}
						/>
					</tbody>
				</Table>
			</td>
		</tr>
	);
};

export default KeywordTable;
