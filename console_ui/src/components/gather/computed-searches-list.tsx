import React, { FC } from "react";
import { Box, Table, Text, Anchor } from "@mantine/core";
import { templateString } from "src/utils/constants";
import { IconExternalLink } from "@tabler/icons-react";
import { useTranslate } from "@refinedev/core";

interface Props {
	list: string[];
	template_url_for_input?: string;
	link?: boolean;
}

const ComputedSearchesURLs: FC<Props> = ({
	list = [],
	template_url_for_input,
	link = true,
}) => {
	const translate = useTranslate();
	// Helper function to parse each query string
	const parseQuery = (query: string) => {
		const handle = query.match(/from:([^\s]+)/)?.[1] || "";
		const keyword = query
			.replace(/from:[^\s]+/, "")
			.replace(/since:[^\s]+/, "")
			.replace(/until:[^\s]+/, "")
			.replace(/near:[^\s]+/, "")
			.trim();
		const since = query.match(/since:(\d{4}-\d{2}-\d{2})/)?.[1];
		const until = query.match(/until:(\d{4}-\d{2}-\d{2})/)?.[1];
		const location = query.match(/near:([^\s]+)/)?.[1] || "";
		return { handle, keyword, since, until, location };
	};

	const parsedList = list.map(parseQuery);

	return (
		<Box mt="md">
			<Table striped highlightOnHover withBorder withColumnBorders>
				<thead>
					<tr>
						<th>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.view.computed.handle"
							)}
						</th>
						<th>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.view.computed.keyword"
							)}
						</th>
						<th>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.view.computed.date"
							)}
						</th>
						<th>
							{translate(
								"gathers.types.apify_x_simple_searches_posts_comments.view.computed.location"
							)}
						</th>
						{link && (
							<th>
								{translate(
									"gathers.types.apify_x_simple_searches_posts_comments.view.computed.link"
								)}
							</th>
						)}
					</tr>
				</thead>

				<tbody>
					{parsedList.map((item, idx) => (
						<tr key={idx}>
							<td>{item?.handle ? `@${item.handle}` : ""}</td>
							<td>{item.keyword}</td>
							<td>
								{item.since && item.until
									? `${new Date(item?.since).toLocaleDateString()} – ${new Date(
											item?.until
										).toLocaleDateString()}`
									: ""}
							</td>
							<td className="capitalize">{item.location}</td>
							{link && (
								<td>
									<Anchor
										href={
											template_url_for_input
												? templateString(template_url_for_input, {
														input: list[idx],
													})
												: list[idx]
										}
										target="_blank"
										rel="noopener noreferrer"
										c="blue"
									>
										<IconExternalLink size={16} />
									</Anchor>
								</td>
							)}
						</tr>
					))}
				</tbody>
			</Table>

			{parsedList.length === 0 && (
				<Text c="dimmed" mt="sm" size="sm">
					{translate(
						"gathers.types.apify_x_simple_searches_posts_comments.view.computed.empty"
					)}
				</Text>
			)}
		</Box>
	);
};

export default ComputedSearchesURLs;
