"use client";

import { ScrollArea, Table } from "@mantine/core";
import React, { useEffect, useState } from "react";
import { useTranslate } from "@refinedev/core";
import { ClassifierResponse } from "src/interfaces/classifier";
import ClassifierRow from "@components/project/classify-row";
import Pagination from "./pagination";

const ClassifierTable: React.FC<{
	refetch: () => void;
	data: any[];
}> = ({ refetch, data }) => {
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
							<th>{translate("gathers.fields.started_run_at")}</th>
							<th>{translate("gathers.fields.completed_at")}</th>
							<th>{translate("projects.fields.status")}</th>
							<th>{translate("table.actions")}</th>
						</tr>
					</thead>
					<tbody>
						{dataSource.map((classifier: ClassifierResponse) => (
							<ClassifierRow
								key={classifier.id}
								row={classifier}
								refetch={refetch}
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

export default ClassifierTable;
