"use client";

import React, { useEffect, useState } from "react";
import { Group, Anchor, Breadcrumbs } from "@mantine/core";
import { useOne } from "@refinedev/core";
import Link from "next/link";

interface BreadcrumbItem {
	title: string;
	href: string;
	replaceWithProjectName?: boolean;
}

interface BreadcrumbsProps {
	breadcrumbs: BreadcrumbItem[];
	projectid?: string;
	setProjectInfo?: any;
}

const BreadcrumbsComponent: React.FC<BreadcrumbsProps> = ({
	breadcrumbs,
	projectid,
	setProjectInfo,
}) => {
	const [updatedBreadcrumbs, setUpdatedBreadcrumbs] =
		useState<BreadcrumbItem[]>(breadcrumbs);

	const { result: projectData } = useOne({
		resource: "projects",
		id: projectid as string,
		queryOptions: {
			enabled: !!projectid,
		},
	});

	useEffect(() => {
		setProjectInfo?.(projectData);
		if (projectData?.name) {
			const newBreadcrumbs = breadcrumbs.map((breadcrumb) => {
				if (breadcrumb?.replaceWithProjectName && projectid) {
					return { ...breadcrumb, title: projectData.name };
				}
				return breadcrumb;
			});
			setUpdatedBreadcrumbs(newBreadcrumbs);
		}
	}, [projectData, breadcrumbs, projectid, setProjectInfo]);

	return (
		<Breadcrumbs>
			{updatedBreadcrumbs.map((item) => (
				<Group key={item.title}>
					<Anchor
						component={Link as any}
						color="gray"
						size="sm"
						href={item.href}
					>
						{item.title}
					</Anchor>
				</Group>
			))}
		</Breadcrumbs>
	);
};

export default BreadcrumbsComponent;
