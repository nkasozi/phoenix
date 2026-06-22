"use client";

import { Authenticated, CanAccess, Refine } from "@refinedev/core";
import { DevtoolsProvider } from "@refinedev/devtools";
import {
	RefineThemes,
	ThemedLayout as ThemedLayoutV2,
	ThemedTitle as ThemedTitleV2,
	useNotificationProvider,
} from "@refinedev/mantine";
import routerProvider from "@refinedev/nextjs-router";
import React, { PropsWithChildren } from "react";
import "@styles/global.css";

import {
	ColorScheme,
	ColorSchemeProvider,
	Global,
	MantineProvider,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { NotificationsProvider } from "@mantine/notifications";
import dataProvider from "@providers/data-provider";
import { IconUser } from "@tabler/icons-react";
import authProvider from "@providers/auth-provider";
import accessControlProvider from "@providers/access-provider";
import Header from "@components/header";
import { useTranslation } from "next-i18next";
import Image from "next/image";

// initialize i18n
import "../providers/i18n";

// Import Date Locales
import "dayjs/locale/en";
import "dayjs/locale/fr";
import "dayjs/locale/es";
import "dayjs/locale/ar";

const RefineContext = ({ children }: PropsWithChildren) => {
	const { t, i18n } = useTranslation();

	const i18nProvider = {
		translate: (key: string, params: object) => t(key, params),
		changeLocale: (lang: string) => i18n.changeLanguage(lang),
		getLocale: () => i18n.language,
	};

	const [colorScheme, setColorScheme] = useLocalStorage<ColorScheme>({
		key: "mantine-color-scheme",
		defaultValue: "light",
		getInitialValueInEffect: true,
	});
	const toggleColorScheme = (value?: ColorScheme) =>
		setColorScheme(value || (colorScheme === "dark" ? "light" : "dark"));

	return (
		<ColorSchemeProvider
			colorScheme={colorScheme}
			toggleColorScheme={toggleColorScheme}
		>
			{/* You can change the theme colors here. example: theme={{ ...RefineThemes.Magenta, colorScheme:colorScheme }} */}
			<MantineProvider
				theme={{ ...RefineThemes.Blue, colorScheme }}
				withNormalizeCSS
				withGlobalStyles
			>
				<Global styles={{ body: { WebkitFontSmoothing: "auto" } }} />
				<NotificationsProvider position="top-right">
					<DevtoolsProvider>
						<Refine
							routerProvider={routerProvider}
							dataProvider={dataProvider}
							notificationProvider={useNotificationProvider}
							i18nProvider={i18nProvider}
							authProvider={authProvider}
							accessControlProvider={accessControlProvider}
							resources={[
								{
									name: "projects",
									list: "/projects",
									create: "/projects/create",
									edit: "/projects/edit/:id",
									show: "/projects/show/:id",
									meta: {
										canDelete: true,
									},
								},
								{
									name: "apify_facebook_posts",
									create:
										"/projects/:projectid/gathers/apify_facebook_posts/create",
									edit: "/projects/:projectid/gathers/apify_facebook_posts/edit/:id",
									show: "/projects/:projectid/gathers/apify_facebook_posts/:id",
									meta: {
										label: "Apify Facebook Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_facebook_comments",
									create:
										"/projects/:projectid/gathers/apify_facebook_comments/create",
									edit: "/projects/:projectid/gathers/apify_facebook_comments/edit/:id",
									show: "/projects/:projectid/gathers/apify_facebook_comments/:id",
									meta: {
										label: "Apify Facebook Comments",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_facebook_search_posts",
									create:
										"/projects/:projectid/gathers/apify_facebook_search_posts/create",
									edit: "/projects/:projectid/gathers/apify_facebook_search_posts/edit/:id",
									show: "/projects/:projectid/gathers/apify_facebook_search_posts/:id",
									meta: {
										label: "Apify Facebook Search Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_tiktok_accounts_posts",
									create:
										"/projects/:projectid/gathers/apify_tiktok_accounts_posts/create",
									edit: "/projects/:projectid/gathers/apify_tiktok_accounts_posts/edit/:id",
									show: "/projects/:projectid/gathers/apify_tiktok_accounts_posts/:id",
									meta: {
										label: "Apify Tiktok Accounts Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_tiktok_hashtags_posts",
									create:
										"/projects/:projectid/gathers/apify_tiktok_hashtags_posts/create",
									edit: "/projects/:projectid/gathers/apify_tiktok_hashtags_posts/edit/:id",
									show: "/projects/:projectid/gathers/apify_tiktok_hashtags_posts/:id",
									meta: {
										label: "Apify Tiktok Accounts Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_tiktok_comments",
									create:
										"/projects/:projectid/gathers/apify_tiktok_comments/create",
									edit: "/projects/:projectid/gathers/apify_tiktok_comments/edit/:id",
									show: "/projects/:projectid/gathers/apify_tiktok_comments/:id",
									meta: {
										label: "Apify Tiktok Comments",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_tiktok_searches_posts",
									create:
										"/projects/:projectid/gathers/apify_tiktok_searches_posts/create",
									edit: "/projects/:projectid/gathers/apify_tiktok_searches_posts/edit/:id",
									show: "/projects/:projectid/gathers/apify_tiktok_searches_posts/:id",
									meta: {
										label: "Apify Tiktok Searches Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "danek_facebook_searches_posts",
									create:
										"/projects/:projectid/gathers/danek_facebook_searches_posts/create",
									edit: "/projects/:projectid/gathers/danek_facebook_searches_posts/edit/:id",
									show: "/projects/:projectid/gathers/danek_facebook_searches_posts/:id",
									meta: {
										label: "Danek Facebook Searches Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "danek_instagram_posts",
									create:
										"/projects/:projectid/gathers/danek_instagram_posts/create",
									edit: "/projects/:projectid/gathers/danek_instagram_posts/edit/:id",
									show: "/projects/:projectid/gathers/danek_instagram_posts/:id",
									meta: {
										label: "Danek Instagram Posts",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "danek_instagram_comments",
									create:
										"/projects/:projectid/gathers/danek_instagram_comments/create",
									edit: "/projects/:projectid/gathers/danek_instagram_comments/edit/:id",
									show: "/projects/:projectid/gathers/danek_instagram_comments/:id",
									meta: {
										label: "Danek Instagram Comments",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "manual_upload",
									create: "/projects/:projectid/gathers/manual_upload/create",
									show: "/projects/:projectid/gathers/manual_upload/:id",
									meta: {
										label: "Manual Upload Gather",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "keyword_match",
									create:
										"/projects/:projectid/classifiers/keyword_match/create",
									edit: "/projects/:projectid/classifiers/keyword_match/edit/:id",
									show: "/projects/:projectid/classifiers/keyword_match/:id",
									meta: {
										label: "Classify Keyword Match",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "manual_post_authors",
									create:
										"/projects/:projectid/classifiers/manual_post_authors/create",
									edit: "/projects/:projectid/classifiers/manual_post_authors/edit/:id",
									show: "/projects/:projectid/classifiers/manual_post_authors/:id",
									meta: {
										label: "Classify Post Authors",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "perspective_api",
									create:
										"/projects/:projectid/classifiers/perspective_api/create",
									edit: "/projects/:projectid/classifiers/perspective_api/edit/:id",
									show: "/projects/:projectid/classifiers/perspective_api/:id",
									meta: {
										label: "Perspective API",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "hugging_face",
									create:
										"/projects/:projectid/classifiers/hugging_face/create",
									show: "/projects/:projectid/classifiers/hugging_face/:id",
									meta: {
										label: "Hugging Face Classifier",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_x_simple_searches_posts_comments",
									create:
										"/projects/:projectid/gathers/apify_x_simple_searches_posts_comments/create",
									edit: "/projects/:projectid/gathers/apify_x_simple_searches_posts_comments/edit/:id",
									show: "/projects/:projectid/gathers/apify_x_simple_searches_posts_comments/:id",
									meta: {
										label: "Apify X Simple Searches Posts & Comments",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "apify_x_advanced_searches_posts_comments",
									create:
										"/projects/:projectid/gathers/apify_x_advanced_searches_posts_comments/create",
									edit: "/projects/:projectid/gathers/apify_x_advanced_searches_posts_comments/edit/:id",
									show: "/projects/:projectid/gathers/apify_x_advanced_searches_posts_comments/:id",
									meta: {
										label: "Apify X Advancesd Searches Posts & Comments",
										parent: "projects",
										hide: true,
									},
								},
								{
									name: "profile",
									list: "/profile",
									meta: {
										label: t("pages.profile.profile"),
										icon: <IconUser size="16" />,
									},
								},
								{
									name: "coming-soon",
									list: "/coming-soon",
									meta: {
										label: "Coming Soon",
										hide: true,
									},
								},
							]}
							options={{
								syncWithLocation: true,
								warnWhenUnsavedChanges: true,
								projectId: "nMl5vA-MzwgF4-ONcYky",
							}}
						>
							<Authenticated key="app">
								<CanAccess>
									<ThemedLayoutV2
										Header={() => <Header sticky />}
										Title={({ collapsed }) => (
											<ThemedTitleV2
												collapsed={collapsed}
												text={t("documentTitle.default")}
												icon={
													<Image
														src="/logo_buildup.png"
														width={32}
														height={32}
														alt="logo"
													/>
												}
											/>
										)}
									>
										{children}
									</ThemedLayoutV2>
								</CanAccess>
							</Authenticated>
						</Refine>
					</DevtoolsProvider>
				</NotificationsProvider>
			</MantineProvider>
		</ColorSchemeProvider>
	);
};

export default RefineContext;
