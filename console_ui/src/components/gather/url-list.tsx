import { Box, Button, Divider, Group, Text } from "@mantine/core";
import { IconExternalLink } from "@tabler/icons-react";
import React, { FC } from "react";
import { templateString } from "src/utils/constants";

interface Props {
	link?: boolean;
	list: [];
	template_url_for_input?: string;
}

const URLInputList: FC<Props> = ({
	link = true,
	list,
	template_url_for_input,
}) => (
	<Box
		py={8}
		sx={{
			border: "1px solid rgba(0, 0, 0, 0.1)",
			maxWidth: "fit-content",
		}}
	>
		{list.map((item: string, idx: number) => (
			<div key={item} className="pt-2">
				<div className="flex items-center justify-between gap-10 px-4">
					<Text>{item}</Text>
					<Group>
						{link && (
							<Button
								component="a"
								href={
									template_url_for_input
										? templateString(template_url_for_input, {
												input: item,
											})
										: item
								}
								target="_blank"
								rel="noopener noreferrer"
								p={0}
								variant="subtle"
							>
								<IconExternalLink size={16} />
							</Button>
						)}
					</Group>
				</div>
				{idx < list.length - 1 && <Divider className="mt-2" />}
			</div>
		))}
	</Box>
);

export default URLInputList;
