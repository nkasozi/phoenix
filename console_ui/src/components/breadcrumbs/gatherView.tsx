import { useTranslate } from "@refinedev/core";
import React from "react";
import BreadcrumbsComponent from ".";

interface Props {
	projectid: string;
	record: any;
	setProjectInfo: any;
}

const GatherViewBreadcrumb: React.FC<Props> = ({
	projectid,
	record,
	setProjectInfo,
}) => {
	const translate = useTranslate();
	const breadcrumbs = [
		{ title: translate("projects.projects"), href: "/projects" },
		{
			title: projectid as string,
			href: `/projects/show/${projectid}`,
			replaceWithProjectName: true,
		},
		{
			title: translate("gathers.gathers"),
			href: `/projects/show/${projectid}?activeItem=gather`,
		},
		{ title: record?.name, href: "" },
	];
	return (
		<BreadcrumbsComponent
			breadcrumbs={breadcrumbs}
			projectid={projectid as string}
			setProjectInfo={setProjectInfo}
		/>
	);
};

export default GatherViewBreadcrumb;
