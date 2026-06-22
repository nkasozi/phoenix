import { useTranslate } from "@refinedev/core";
import React from "react";
import BreadcrumbsComponent from ".";

interface Props {
	projectid: string;
	record: any;
}

const ClassifierViewBreadcrumb: React.FC<Props> = ({ projectid, record }) => {
	const translate = useTranslate();
	const breadcrumbs = [
		{ title: translate("projects.projects"), href: "/projects" },
		{
			title: projectid as string,
			href: `/projects/show/${projectid}`,
			replaceWithProjectName: true,
		},
		{
			title: translate("classifiers.classifiers"),
			href: `/projects/show/${projectid}?activeItem=classify`,
		},
		{
			title: record?.name,
			href: `/projects/${projectid}/classifiers/${record?.type}/${record?.id}`,
		},
	];
	return (
		<BreadcrumbsComponent
			breadcrumbs={breadcrumbs}
			projectid={projectid as string}
		/>
	);
};

export default ClassifierViewBreadcrumb;
