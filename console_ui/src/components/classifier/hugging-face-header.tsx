"use client";

import { Anchor } from "@mantine/core";
import { useTranslate } from "@refinedev/core";
import React from "react";

interface Props {}

const HuggingFaceClassifierHeader: React.FC<Props> = () => {
	const translate = useTranslate();
	return (
		<>
			<p className="mb-2">
				<Anchor
					className="font-normal text-inherit !text-blue-500 text-sm underline"
					href="https://huggingface.co"
					target="_blank"
				>
					{translate(
						"classifiers.types.hugging_face.create_page.description1a"
					)}
				</Anchor>
				{translate("classifiers.types.hugging_face.create_page.description1b")}
			</p>
			<p className="mb-2">
				{translate("classifiers.types.hugging_face.create_page.description2")}
			</p>
			<p className="mb-2">
				{translate("classifiers.types.hugging_face.create_page.description3")}
			</p>
			<p className="mb-4">
				{translate("classifiers.types.hugging_face.create_page.description4")}
			</p>
		</>
	);
};

export default HuggingFaceClassifierHeader;
