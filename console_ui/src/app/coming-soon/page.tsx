"use client";

import { Authenticated, useTranslate } from "@refinedev/core";
import { Suspense } from "react";
import Link from "next/link";

export default function ComingSoon() {
	const translate = useTranslate();

	return (
		<div style={{ textAlign: "center", marginTop: "20%" }}>
			<h1>{translate("pages.coming_soon.title")}</h1>
			<p>{translate("pages.coming_soon.message")}</p>
			<Link
				href="https://gitlab.com/howtobuildup/phoenix/-/milestones"
				target="_blank"
				rel="noopener noreferrer"
			>
				{translate("pages.coming_soon.link_text")}
			</Link>
		</div>
	);
}
