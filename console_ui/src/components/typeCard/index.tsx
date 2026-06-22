"use client";

import React from "react";
import { Button } from "@mantine/core";
import Link from "next/link";

const TypeCard = ({
	icon,
	title,
	description,
	link_text = "Proceed",
	link,
}: {
	icon?: React.ReactNode;
	title: string;
	description: any;
	link_text?: string;
	link: string;
}) => (
	<div className="p-6 md:w-[300px] w-full mx-auto bg-white border border-gray-100 shadow-md flex flex-col items-start">
		{icon && <div className="mb-7 mt-4">{icon}</div>}
		<div className="flex flex-col justify-between h-full">
			<div>
				<div className="text-xl font-medium mb-3 text-black">{title}</div>
				<p className="text-gray-500">{description}</p>
			</div>
			<Link href={link} className="no-underline">
				<Button
					pl={0}
					variant="subtle"
					className="mt-6 flex items-center hover:bg-transparent"
				>
					{link_text} <span className="ml-2">→</span>
				</Button>
			</Link>
		</div>
	</div>
);

export default TypeCard;
