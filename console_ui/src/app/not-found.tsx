"use client";

import { ErrorComponent } from "@refinedev/mantine";
import { Authenticated } from "@refinedev/core";
import { Suspense } from "react";

export default function NotFound() {
	return (
		<Suspense>
			<Authenticated key="not-found">
				<ErrorComponent />
			</Authenticated>
		</Suspense>
	);
}
