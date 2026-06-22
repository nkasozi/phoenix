"use client";

import { Modal, Button } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { useTranslate } from "@refinedev/core";
import { useState } from "react";
import { GatherResponse } from "src/interfaces/gather";
import { gatherService } from "src/services";

interface Props {
	opened: boolean;
	setOpened: any;
	gatherDetail: any;
	refetch: any;
}

const GatherDeleteModal: React.FC<Props> = ({
	opened,
	setOpened,
	gatherDetail,
	refetch,
}) => {
	const translate = useTranslate();
	const [loading, setLoading] = useState(false);

	const handleClose = () => {
		setOpened(false);
	};

	const handleDelete = () => {
		setLoading(true);
		gatherService
			.deleteGather({
				project_id: gatherDetail.project_id,
				id: gatherDetail.id,
			})
			.then((res) => {
				refetch();
				showNotification({
					title: "Success",
					message: translate("gathers.success.delete"),
				});
				handleClose();
				setLoading(false);
			})
			.catch((err) => {
				showNotification({
					title: "Error",
					message: err.message || translate("gathers.error.delete"),
					color: "red",
				});
				setLoading(false);
			});
	};
	return (
		<Modal
			opened={opened}
			size="lg"
			onClose={handleClose}
			withCloseButton={false}
		>
			<div className="font-medium flex flex-col px-8 pb-8">
				<h3 className="flex w-full items-center mb-1">
					<span className="font-medium text-xl">
						{translate("buttons.delete")} {gatherDetail?.name}
					</span>
				</h3>
				{/* Translate these */}
				<p className="text-[#404040] text-sm font-normal">
					{translate("gathers.delete.message")}
				</p>
				<div className="text-neutral-500 text-sm font-normal">
					<p className="mb-1">{translate("gathers.delete.note")}</p>
					<ul className="list-disc pl-5 space-y-1">
						<li>{translate("gathers.delete.list.a")}</li>
						<li>{translate("gathers.delete.list.b")}</li>
						<li>{translate("gathers.delete.list.c")}</li>
					</ul>
				</div>

				<div className="flex gap-4 justify-end mt-5" role="group">
					<Button variant="subtle" onClick={handleClose}>
						{translate("buttons.cancel")}
					</Button>
					<Button
						onClick={handleDelete}
						loading={loading}
						disabled={loading}
						color="red"
					>
						{translate("buttons.delete")}
					</Button>
				</div>
			</div>
		</Modal>
	);
};

export default GatherDeleteModal;
