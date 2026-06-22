"use client";

import { Modal, Button, Text, FileInput, Radio } from "@mantine/core";
import { IconUpload } from "@tabler/icons-react";
import { showNotification } from "@mantine/notifications";
import { useTranslate } from "@refinedev/core";
import { useState } from "react";
import { classifierService } from "src/services";
import { normaliseErrorMessage } from "src/utils";

interface Props {
	opened: boolean;
	setOpened: (value: boolean) => void;
	projectId: string;
	classifierId: string;
	onSuccess: () => void;
}

const ClassifierImportCsvModal: React.FC<Props> = ({
	opened,
	setOpened,
	projectId,
	classifierId,
	onSuccess,
}) => {
	const translate = useTranslate();
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [file, setFile] = useState<File | null>(null);
	const [importMode, setImportMode] = useState<string | null>(null);

	const handleClose = () => {
		setOpened(false);
		setError(null);
		setFile(null);
		setImportMode(null);
	};

	const handleImport = async () => {
		if (!file || !importMode) return;
		setLoading(true);
		setError(null);
		try {
			await classifierService.importKeywordConfigCsv(
				{
					project_id: projectId,
					classifier_id: classifierId,
				},
				file,
				importMode
			);
			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.import"),
			});
			onSuccess();
			handleClose();
		} catch (err: any) {
			const message = normaliseErrorMessage(err, translate);
			setError(message);
			showNotification({
				title: translate("status.error"),
				color: "red",
				message,
			});
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
						{translate("classifiers.import_modal.title")}
					</span>
				</h3>

				{error && <span className="text-red-500 mb-4">{error}</span>}

				<Text className="text-base text-neutral-500 font-normal mb-4">
					{translate("classifiers.import_modal.description")}
				</Text>

				<FileInput
					label={translate("classifiers.import_csv")}
					value={file}
					onChange={setFile}
					accept=".csv"
					icon={<IconUpload size={14} />}
					mb="md"
				/>

				<Radio.Group
					label={translate("classifiers.import_modal.mode.label")}
					value={importMode || ""}
					onChange={setImportMode}
					mb="md"
				>
					<div className="flex gap-4 mt-2">
						<Radio
							value="append"
							label={translate("classifiers.import_modal.mode.append")}
						/>
						<Radio
							value="replace"
							label={translate("classifiers.import_modal.mode.replace")}
						/>
					</div>
				</Radio.Group>

				{importMode === "append" && (
					<Text className="text-sm text-neutral-500 font-normal mb-4">
						{translate("classifiers.import_modal.append_info")}
					</Text>
				)}

				{importMode === "replace" && (
					<Text className="text-sm text-red-500 font-normal mb-4">
						{translate("classifiers.import_modal.replace_warning")}
					</Text>
				)}

				<div className="flex justify-end items-center mt-4">
					<div className="flex gap-4" role="group">
						<Button variant="subtle" color="red" onClick={handleClose}>
							{translate("buttons.cancel")}
						</Button>
						<Button
							variant="filled"
							color="blue"
							loading={loading}
							onClick={handleImport}
							disabled={loading || !file || !importMode}
						>
							{translate("classifiers.import_csv")}
						</Button>
					</div>
				</div>
			</div>
		</Modal>
	);
};

export default ClassifierImportCsvModal;
