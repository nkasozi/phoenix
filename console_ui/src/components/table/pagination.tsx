"use client";

import { Pagination } from "@mantine/core";
import React, { useEffect, useState } from "react";

interface Props {
	pages: number;
	_activeIndex: number;
	_setActiveIndex: any;
}
const PaginationComponent: React.FC<Props> = ({
	pages,
	_activeIndex = 1,
	_setActiveIndex,
}) => {
	const [activeIndex, setActiveIndex] = useState(_activeIndex);

	useEffect(() => {
		_setActiveIndex(activeIndex);
	}, [activeIndex, _setActiveIndex]);
	return (
		<Pagination
			position="right"
			total={pages}
			page={activeIndex}
			onChange={setActiveIndex}
		/>
	);
};

export default PaginationComponent;
