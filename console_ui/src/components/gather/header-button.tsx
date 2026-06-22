import { useTranslate } from "@refinedev/core";
import React from "react";
import Link from "next/link";
import { EditButton, EditButtonProps } from "@refinedev/mantine";
import { Button } from "@mantine/core";
import { IconCopy } from "@tabler/icons-react";

interface Props {
	resource: string;
	id: string;
	projectid: string;
	record: any;
	isLoading: boolean;
}

const GatherViewHeaderButton: React.FC<Props> = ({
	resource,
	id,
	projectid,
	record,
	isLoading,
}) => {
	const translate = useTranslate();
	const editButtonProps: EditButtonProps = {
		resource,
		recordItemId: id as string,
		...(isLoading || record?.latest_job_run ? { disabled: true } : {}),
	};
	return (
		<>
			<Link href={`/projects/${projectid}/gathers/${resource}/duplicate/${id}`}>
				<Button leftIcon={<IconCopy size={18} />}>
					{translate("buttons.duplicate")}
				</Button>
			</Link>
			<EditButton {...editButtonProps} />
		</>
	);
};

export default GatherViewHeaderButton;
