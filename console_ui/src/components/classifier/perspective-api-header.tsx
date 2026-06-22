"use client";

import { Anchor } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import React from "react";

interface Props {}

const PerspectiveApiHeader: React.FC<Props> = () => {
	const translate = useTranslate();
	return (
		<>
			<p className="mb-2">
				<Anchor
					className="font-normal text-inherit !text-blue-500 text-sm underline"
					href="https://perspectiveapi.com/"
					target="_blank"
				>
					{translate(
						"classifiers.types.perspective_api.create_page.description1a"
					)}
				</Anchor>
				{translate(
					"classifiers.types.perspective_api.create_page.description1b"
				)}
			</p>
			<p className="mb-2">
				{translate(
					"classifiers.types.perspective_api.create_page.description2"
				)}
			</p>
			<p className="mb-2">
				{translate(
					"classifiers.types.perspective_api.create_page.description3"
				)}
			</p>
			<p className="mb-4">
				{translate(
					"classifiers.types.perspective_api.create_page.description4"
				)}
				<Anchor
					className="font-normal text-inherit !text-blue-500 text-sm underline"
					href="https://developers.perspectiveapi.com/s/about-the-api-attributes-and-languages"
					target="_blank"
				>
					{translate(
						"classifiers.types.perspective_api.create_page.description5"
					)}
				</Anchor>
			</p>
		</>
	);
};

export default PerspectiveApiHeader;
