"use client";

import { ScrollArea, Table, Tooltip } from "@mantine/core";
import { IconInfoCircle } from "@tabler/icons-react";
import React, { useEffect, useState } from "react";
import { useTranslate } from "@refinedev/core";
import { GatherResponse } from "src/interfaces/gather";
import GatherRow from "@components/project/gather-row";
import Pagination from "./pagination";

const GatherTable: React.FC<{
	data: any[];
	setSelected: any;
	setDeleteModalOpen: any;
}> = ({ data, setSelected, setDeleteModalOpen }) => {
	const translate = useTranslate();
	const [dataSource, setDataSource] = useState<any[]>([]);
	const [pages, setPages] = useState<number>(1);
	const [activeIndex, setActiveIndex] = useState<number>(1);

	useEffect(() => {
		if (data) {
			const allData = data;
			const pageSize = 10;
			const currentPageData = allData.slice(
				(activeIndex - 1) * pageSize,
				activeIndex * pageSize
			);

			setDataSource(currentPageData);
			setPages(Math.ceil(allData.length / pageSize));
		}
	}, [activeIndex, data]);
	return (
		<>
			<ScrollArea>
				<Table highlightOnHover>
					<thead>
						<tr>
							<th>{translate("gathers.fields.name")}</th>
							<th>{translate("gathers.fields.completed_at")}</th>
							<th>{translate("gathers.fields.total_cost")}</th>
							<th>
								<div className="flex items-center">
									{translate("gathers.fields.result_count")}
									<Tooltip
										label={translate("gathers.fields.result_count_tooltip")}
										width={200}
										multiline
									>
										<span className="flex">
											<IconInfoCircle size={12} />
										</span>
									</Tooltip>
								</div>
							</th>
							<th>
								<div className="flex items-center">
									{translate("gathers.fields.error_count")}
									<Tooltip
										label={translate("gathers.fields.error_count_tooltip")}
										width={200}
										multiline
									>
										<span className="flex">
											<IconInfoCircle size={12} />
										</span>
									</Tooltip>
								</div>
							</th>
							<th>{translate("projects.fields.status")}</th>
							<th>{translate("table.actions")}</th>
						</tr>
					</thead>
					<tbody>
						{dataSource.map((gather: GatherResponse) => (
							<GatherRow
								key={gather.id}
								row={gather}
								setSelected={setSelected}
								setDeleteModalOpen={setDeleteModalOpen}
								translate={translate}
							/>
						))}
					</tbody>
				</Table>
			</ScrollArea>
			<br />
			<Pagination
				pages={pages}
				_activeIndex={activeIndex}
				_setActiveIndex={setActiveIndex}
			/>
		</>
	);
};

export default GatherTable;
