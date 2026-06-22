"use client";

import { Table, Tooltip, Anchor, Checkbox } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";

interface KeywordConfig {
	id: number;
	class_id: number;
	musts: string;
	nots?: string;
	is_regex?: boolean;
}

interface KeywordTableViewProps {
	keywordGroups: KeywordConfig[];
	translate: (key: string) => string;
}

const KeywordTableView: React.FC<KeywordTableViewProps> = ({
	keywordGroups,
	translate,
}) => {
	return (
		<tr>
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
						</tr>
					</thead>
					<tbody>
						{keywordGroups.map((keywordGroup, keywordIndex) => (
							<tr key={keywordIndex}>
								<td>{keywordGroup.musts}</td>
								<td>
									<Checkbox
										size="xs"
										checked={keywordGroup.is_regex || false}
										readOnly
									/>
								</td>
							</tr>
						))}
					</tbody>
				</Table>
			</td>
		</tr>
	);
};

export default KeywordTableView;
