"use client";

import { useTranslate } from "@refinedev/core";
import { Button } from "@mantine/core";
import { IconEye } from "@tabler/icons-react";
import Link from "next/link";

interface DashboardLinkButtonProps {
	workspaceSlug: string;
	platformDomainBase?: string;
	platformSchemaBase?: string;
	dashboardId?: string;
}

const PLATFORM_DOMAIN_BASE = process.env.NEXT_PUBLIC_PLATFORM_DOMAIN_BASE!;
const PLATFORM_SCHEMA_BASE = process.env.NEXT_PUBLIC_PLATFORM_SCHEMA_BASE!;

const DashboardLinkButton: React.FC<DashboardLinkButtonProps> = ({
	workspaceSlug,
	platformDomainBase = PLATFORM_DOMAIN_BASE || "",
	platformSchemaBase = PLATFORM_SCHEMA_BASE || "",
	dashboardId,
}) => {
	const translate = useTranslate();

	if (!platformDomainBase || !platformSchemaBase) {
		return null;
	}

	let href = `${platformSchemaBase}://dashboard.${workspaceSlug}.${platformDomainBase}`;
	if (dashboardId) {
		href += `/superset/dashboard/${dashboardId}/`;
	}

	return (
		<Link href={href} target="_blank">
			<Button leftIcon={<IconEye />}>
				{translate("projects.titles.dashboard")}
			</Button>
		</Link>
	);
};

export default DashboardLinkButton;
