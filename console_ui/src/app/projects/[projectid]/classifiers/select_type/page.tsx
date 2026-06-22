"use client";

import TypeCard from "@components/typeCard";
import { ActionIcon, Anchor, Group, Title } from "@mantine/core";
import { useBack, useTranslate } from "@refinedev/core";
import { IconArrowLeft } from "@tabler/icons-react";
import { useParams } from "next/navigation";

export default function SelectClassifierType(): JSX.Element {
	const back = useBack();
	const { projectid } = useParams();
	const translate = useTranslate();
	return (
		<div className="grow flex flex-col mt-4">
			<Group spacing="xs">
				<ActionIcon onClick={back}>
					<IconArrowLeft />
				</ActionIcon>
				<Title order={3} transform="capitalize" className="flex-1 text-center">
					{translate("classifiers.titles.select_type")}
				</Title>
			</Group>
			<div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-5 mx-4 md:mx-0 justify-center mt-10 self-center">
				<TypeCard
					title={translate("classifiers.types.manual_post_authors.create")}
					description={translate(
						"classifiers.types.manual_post_authors.create_description"
					)}
					link={`/projects/${projectid}/classifiers/manual_post_authors/create`}
					link_text={translate(
						"classifiers.types.manual_post_authors.proceed_text"
					)}
				/>
				<TypeCard
					title={translate("classifiers.types.keyword_match.create")}
					description={translate(
						"classifiers.types.keyword_match.create_description"
					)}
					link={`/projects/${projectid}/classifiers/keyword_match/create`}
					link_text={translate("classifiers.types.keyword_match.proceed_text")}
				/>
				<TypeCard
					title={translate("classifiers.types.hugging_face.create")}
					description={translate(
						"classifiers.types.hugging_face.create_description"
					)}
					link={`/projects/${projectid}/classifiers/hugging_face/create`}
					link_text={translate("classifiers.types.hugging_face.proceed_text")}
				/>
			</div>
		</div>
	);
}
