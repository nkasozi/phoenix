"use client";

import TypeCard from "@components/typeCard";
import { ActionIcon, Divider, Group, Title } from "@mantine/core";
import { useBack, useTranslate } from "@refinedev/core";
import {
	IconArrowLeft,
	IconBrandFacebook,
	IconBrandTiktok,
	IconBrandYoutube,
	IconBrandInstagram,
	IconBrandTelegram,
	IconUpload,
} from "@tabler/icons-react";
import { IconBrandX } from "src/assets";
import { useParams } from "next/navigation";

export default function SelectGatherType(): JSX.Element {
	const back = useBack();
	const { projectid } = useParams();
	const translate = useTranslate();

	// Define all gather types with their properties
	const gatherTypes = [
		{
			id: "apify_facebook_posts",
			icon: <IconBrandFacebook className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_facebook_posts.title",
			descriptionKey: "gathers.types.apify_facebook_posts.description",
			link: `/projects/${projectid}/gathers/apify_facebook_posts/create`,
		},
		{
			id: "apify_facebook_search_posts",
			icon: <IconBrandFacebook className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_facebook_search_posts.title",
			descriptionKey: "gathers.types.apify_facebook_search_posts.description",
			link: `/projects/${projectid}/gathers/apify_facebook_search_posts/create`,
		},
		{
			id: "danek_facebook_searches_posts",
			icon: <IconBrandFacebook className="text-blue-600" size={27} />,
			titleKey: "gathers.types.danek_facebook_searches_posts.title",
			descriptionKey: "gathers.types.danek_facebook_searches_posts.description",
			link: `/projects/${projectid}/gathers/danek_facebook_searches_posts/create`,
		},
		{
			id: "apify_facebook_comments",
			icon: <IconBrandFacebook className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_facebook_comments.title",
			descriptionKey: "gathers.types.apify_facebook_comments.description",
			link: `/projects/${projectid}/gathers/apify_facebook_comments/create`,
		},
		{
			id: "danek_instagram_posts",
			icon: <IconBrandInstagram className="text-blue-600" size={27} />,
			titleKey: "gathers.types.danek_instagram_posts.title",
			descriptionKey: "gathers.types.danek_instagram_posts.description",
			link: `/projects/${projectid}/gathers/danek_instagram_posts/create`,
		},
		{
			id: "danek_instagram_comments",
			icon: <IconBrandInstagram className="text-blue-600" size={27} />,
			titleKey: "gathers.types.danek_instagram_comments.title",
			descriptionKey: "gathers.types.danek_instagram_comments.description",
			link: `/projects/${projectid}/gathers/danek_instagram_comments/create`,
		},
		{
			id: "apify_tiktok_accounts_posts",
			icon: <IconBrandTiktok className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_tiktok_accounts_posts.title",
			descriptionKey: "gathers.types.apify_tiktok_accounts_posts.description",
			link: `/projects/${projectid}/gathers/apify_tiktok_accounts_posts/create`,
		},
		{
			id: "apify_tiktok_searches_posts",
			icon: <IconBrandTiktok className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_tiktok_searches_posts.title",
			descriptionKey: "gathers.types.apify_tiktok_searches_posts.description",
			link: `/projects/${projectid}/gathers/apify_tiktok_searches_posts/create`,
		},
		{
			id: "apify_tiktok_hashtags_posts",
			icon: <IconBrandTiktok className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_tiktok_hashtags_posts.title",
			descriptionKey: "gathers.types.apify_tiktok_hashtags_posts.description",
			link: `/projects/${projectid}/gathers/apify_tiktok_hashtags_posts/create`,
		},
		{
			id: "apify_tiktok_comments",
			icon: <IconBrandTiktok className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_tiktok_comments.title",
			descriptionKey: "gathers.types.apify_tiktok_comments.description",
			link: `/projects/${projectid}/gathers/apify_tiktok_comments/create`,
		},
		{
			id: "apify_x_simple_searches_posts_comments",
			icon: <IconBrandX className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_x_simple_searches_posts_comments.title",
			descriptionKey:
				"gathers.types.apify_x_simple_searches_posts_comments.description",
			link: `/projects/${projectid}/gathers/apify_x_simple_searches_posts_comments/create`,
		},
		{
			id: "apify_x_advanced_searches_posts_comments",
			icon: <IconBrandX className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_x_advanced_searches_posts_comments.title",
			descriptionKey:
				"gathers.types.apify_x_advanced_searches_posts_comments.description",
			link: `/projects/${projectid}/gathers/apify_x_advanced_searches_posts_comments/create`,
		},
		{
			id: "apify_youtube_accounts_posts",
			icon: <IconBrandYoutube className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_youtube_accounts_posts.title",
			descriptionKey: "gathers.types.apify_youtube_accounts_posts.description",
			link: "",
		},
		{
			id: "apify_youtube_search_posts",
			icon: <IconBrandYoutube className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_youtube_search_posts.title",
			descriptionKey: "gathers.types.apify_youtube_search_posts.description",
			link: "",
		},
		{
			id: "apify_youtube_comments",
			icon: <IconBrandYoutube className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_youtube_comments.title",
			descriptionKey: "gathers.types.apify_youtube_comments.description",
			link: "",
		},
		{
			id: "apify_telegram_chats_posts",
			icon: <IconBrandTelegram className="text-blue-600" size={27} />,
			titleKey: "gathers.types.apify_telegram_chats_posts.title",
			descriptionKey: "gathers.types.apify_telegram_chats_posts.description",
			link: "",
		},
		{
			id: "manual_upload",
			icon: <IconUpload className="text-blue-600" size={27} />,
			titleKey: "gathers.types.manual_upload.title",
			descriptionKey: "gathers.types.manual_upload.description",
			link: `/projects/${projectid}/gathers/manual_upload/create`,
		},
	];

	// Get hidden types from environment variable
	const hiddenTypesString = process.env.NEXT_PUBLIC_HIDDEN_GATHER_TYPES || "";
	const hiddenTypes = hiddenTypesString.split(",").map((type) => type.trim());

	// Filter out hidden types
	const visibleTypes = gatherTypes.filter(
		(type) => !hiddenTypes.includes(type.id)
	);

	return (
		<div className="grow flex flex-col mt-4">
			<Group spacing="xs">
				<ActionIcon onClick={back}>
					<IconArrowLeft />
				</ActionIcon>
				<Title order={3} transform="capitalize" className="flex-1 text-center">
					{translate("gathers.titles.select_type")}
				</Title>
			</Group>
			<div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-5 mx-4 md:mx-0 justify-center mt-10 self-center">
				{visibleTypes
					.filter((type) => type.link)
					.map((type) => (
						<TypeCard
							key={type.id}
							icon={type.icon}
							title={translate(type.titleKey)}
							description={translate(type.descriptionKey)}
							link={type.link}
						/>
					))}
			</div>
			<Divider
				my="lg"
				size="sm"
				label={translate("pages.coming_soon.title")}
				labelPosition="center"
			/>
			<div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-5 mx-4 md:mx-0 justify-center self-center">
				{visibleTypes
					.filter((type) => !type.link)
					.map((type) => (
						<TypeCard
							key={type.id}
							icon={type.icon}
							title={translate(type.titleKey)}
							description={translate(type.descriptionKey)}
							link="/coming-soon"
						/>
					))}
			</div>
		</div>
	);
}
