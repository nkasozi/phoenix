import React, { Suspense } from "react";
import { Metadata } from "next";
import { cookies } from "next/headers";
import RefineContext from "./_refine_context";
import "@styles/global.css";

export const metadata: Metadata = {
	title: "Phoenix",
	description: "Console",
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	const cookieStore = cookies();
	const lang = cookieStore.get("NEXT_LOCALE");
	return (
		<html lang={lang?.value || "en"}>
			<body>
				<Suspense>
					<RefineContext>{children}</RefineContext>
				</Suspense>
			</body>
		</html>
	);
}
