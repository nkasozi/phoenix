"use client";

import React, { useEffect, useState } from "react";
import { flexRender } from "@tanstack/react-table";
import { Table, Skeleton, ScrollArea } from "@mantine/core";
import { useTable } from "@refinedev/react-table";
import Pagination from "./pagination";

interface ITableProps {
	columns: any;
	data: any;
}

const TableComponent: React.FC<ITableProps> = ({ columns, data }) => {
	const [dataSource, setDataSource] = useState<any[]>([]);
	const [pages, setPages] = useState<number>(1);
	const [activeIndex, setActiveIndex] = useState<number>(1);
	const {
		reactTable: { getHeaderGroups, getRowModel, setPageIndex },
	} = useTable({
		columns,
		data: dataSource,
		refineCoreProps: {
			pagination: {
				mode: "client",
			},
		},
	});
	const {
		refineCore: { tableQuery: tableQueryResult },
	} = useTable({
		columns,
	});

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
		setPageIndex(activeIndex);
	}, [activeIndex, data, setPageIndex]);

	if (data?.isLoading) {
		return <Skeleton />;
	}

	return (
		<>
			<ScrollArea>
				<Table highlightOnHover>
					<thead>
						{getHeaderGroups().map((headerGroup) => (
							<tr key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<th key={header.id}>
										{!header.isPlaceholder &&
											flexRender(
												header.column.columnDef.header,
												header.getContext()
											)}
									</th>
								))}
							</tr>
						))}
					</thead>
					<tbody>
						{getRowModel().rows.map((row) => (
							<tr key={row.id}>
								{row.getVisibleCells().map((cell) => (
									<td key={cell.id}>
										{flexRender(cell.column.columnDef.cell, cell.getContext())}
									</td>
								))}
							</tr>
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

export default TableComponent;
