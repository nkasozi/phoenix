"use client";

import { Modal, Button, Text, Group } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { useTranslate } from "@refinedev/core";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { classifierService } from "src/services";
import { normaliseErrorMessage } from "src/utils";

interface Props {
	opened: boolean;
	setOpened: (value: boolean) => void;
	classifierDetail: any;
	refetch: () => void;
}

const ClassifierRunModal: React.FC<Props> = ({
	opened,
	setOpened,
	classifierDetail,
	refetch,
}) => {
	const router = useRouter();
	const translate = useTranslate();
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const handleClose = () => {
		setOpened(false);
		setError(null);
	};

	const handleApplyClassifier = async (): Promise<void> => {
		setLoading(true);
		try {
			const { project_id, id, type } = classifierDetail;

			if (type === "keyword_match") {
				await classifierService.runKeywordClassifier({
					project_id,
					classifier_id: id,
				});
			} else if (type === "manual_post_authors") {
				await classifierService.runManualPostAuthorsClassifier({
					project_id,
					classifier_id: id,
				});
			}

			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.success"),
			});

			refetch();
			handleClose();
			router.replace(`/projects/show/${project_id}?activeItem=classify`);
		} catch (err: any) {
			showNotification({
				title: translate("status.error"),
				color: "red",
				message: normaliseErrorMessage(err, translate),
			});
			setError(err?.response?.data?.message || "An error occurred");
		} finally {
			setLoading(false);
		}
	};

	return (
		<Modal
			opened={opened}
			size="lg"
			onClose={handleClose}
			withCloseButton={false}
		>
			<div className="font-medium flex flex-col px-8 pb-8">
				<h3 className="flex w-full items-center mb-6">
					<span className="font-medium text-xl">
						{translate("classifiers.run_modal.title")}
					</span>
				</h3>

				{error && <span className="text-red-500">{error}</span>}

				<Group className="w-full mb-5 p-1">
					<Text className="text-base text-neutral-500 font-normal">
						{translate("gathers.fields.name")}:
					</Text>
					<Text className="font-medium text-lg">{classifierDetail?.name}</Text>
				</Group>

				<div className="p-1 flex flex-col gap-4 mb-6">
					{["text1", "text2", "text3", "text4"].map((key) => (
						<Text key={key} className="text-base text-neutral-500 font-normal">
							{translate(`classifiers.run_modal.${key}`)}
						</Text>
					))}
				</div>

				<div className="flex justify-end items-center mt-4">
					<div className="flex gap-4" role="group">
						<Button variant="subtle" color="red" onClick={handleClose}>
							{translate("buttons.cancel")}
						</Button>
						<Button
							variant="filled"
							color="blue"
							loading={loading}
							onClick={handleApplyClassifier}
							disabled={loading}
						>
							{translate("classifiers.run")}
						</Button>
					</div>
				</div>
			</div>
		</Modal>
	);
};

export default ClassifierRunModal;
