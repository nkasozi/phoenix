"use client";

import {
	TextInput,
	Button,
	Table,
	Tooltip,
	ActionIcon,
	Space,
	Divider,
	Loader,
} from "@mantine/core";
import {
	IconTrash,
	IconPlus,
	IconCheck,
	IconChevronDown,
	IconChevronUp,
	IconDownload,
	IconUpload,
	IconExclamationMark,
} from "@tabler/icons-react";
import {
	useState,
	useEffect,
	useMemo,
	useRef,
	ChangeEvent,
	useCallback,
	Fragment,
} from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslate } from "@refinedev/core";
import { classifierService } from "src/services";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import ClassifierImportCsvModal from "@components/modals/classifier-import-csv";
import KeywordTable from "./KeywordTable";
import { useKeywordClassifierMutations } from "./useKeywordClassifierMutations";
import { useSaveStatus } from "./useSaveStatus";

// Define types for class and keyword group structures
interface ClassData {
	id?: number;
	clientId: string;
	name: string;
	description: string;
}

interface KeywordGroup {
	id?: number; // Will exist for existing configurations, undefined for new ones
	clientId: string;
	class_id: number;
	musts: string;
	nots?: string;
	is_regex?: boolean;
	class_name?: string;
}

const EditKeywordClassifier: React.FC = () => {
	const router = useRouter();
	const translate = useTranslate();
	const { projectid, id } = useParams();
	const mutations = useKeywordClassifierMutations(
		projectid as string,
		id as string
	);
	const saveStatus = useSaveStatus();
	// State to manage classes and keyword groups
	const [classifierName, setClassifierName] = useState("");
	const [classifierDescription, setClassifierDescription] = useState("");
	const [classifier, setClassifier] = useState<any>();
	const [classes, setClasses] = useState<ClassData[]>([]);
	const [keywordGroups, setKeywordGroups] = useState<KeywordGroup[]>([]);
	const [isModified, setIsModified] = useState<boolean>(false);
	const [isBasicModified, setIsBasicModified] = useState<boolean>(false);
	const [openRows, setOpenRows] = useState<{ [key: string]: boolean }>({});
	const [importOpened, setImportOpened] = useState<boolean>(false);
	const [newKeywordMusts, setNewKeywordMusts] = useState<{
		[key: number]: string;
	}>({});
	const [newKeywordIsRegex, setNewKeywordIsRegex] = useState<{
		[key: number]: boolean;
	}>({});
	const [newClassName, setNewClassName] = useState("");
	const [newClassDescription, setNewClassDescription] = useState("");
	const [isBasicInfoSaving, setIsBasicInfoSaving] = useState(false);

	// Derive unsaved state from actual pending edits
	const hasUnsavedNewKeywords = useMemo(
		() => Object.values(newKeywordMusts).some((v) => v.trim() !== ""),
		[newKeywordMusts]
	);
	const hasUnsavedChanges =
		isModified || isBasicModified || hasUnsavedNewKeywords;
	const shouldWarnOnLeave = hasUnsavedChanges || saveStatus.hasPendingSaves();

	// Refs for latest state so debounced callbacks never read stale closures
	const classesRef = useRef(classes);
	classesRef.current = classes;
	const keywordGroupsRef = useRef(keywordGroups);
	keywordGroupsRef.current = keywordGroups;

	const showRow = (key: string) => {
		setOpenRows((prev) => ({ ...prev, [key]: true }));
	};

	const toggleRow = (key: string) => {
		setOpenRows((prev) => ({ ...prev, [key]: !prev[key] }));
	};

	const navigateWithConfirmation = (url: string) => {
		if (shouldWarnOnLeave) {
			const confirmed = window.confirm(
				translate("notifications.unsaved_changes")
			);
			if (!confirmed) return;
		}
		router.push(url);
	};

	// Fetch initial data on mount
	const fetchData = useCallback(async () => {
		try {
			const { data } = await classifierService.getClassifierData({
				project_id: projectid as string,
				classifier_id: id as string,
			});
			setClassifier(data);
			setClassifierName(data?.name);
			setClassifierDescription(data?.description);
			// Set classes and keyword groups from API response
			setClasses(
				data.intermediatory_classes.map((cls: any) => ({
					...cls,
					clientId: String(cls.id),
				}))
			);
			setKeywordGroups(
				data.intermediatory_class_to_keyword_configs.map((kg: any) => ({
					...kg,
					clientId: String(kg.id),
				}))
			);
		} catch (error) {
			console.error("Error fetching classifier data", error);
		}
	}, [id, projectid]);

	useEffect(() => {
		if (id && projectid) {
			fetchData();
		}
	}, [id, projectid, fetchData]);

	useEffect(() => {
		window.onbeforeunload = shouldWarnOnLeave ? () => true : null;
		return () => {
			window.onbeforeunload = null;
		};
	}, [shouldWarnOnLeave]);

	// Flush pending debounced saves on unmount
	useEffect(() => {
		const classSaveRef = autoSaveClassRef.current;
		const kwSaveRef = autoSaveKwRef.current;
		return () => {
			if (classSaveRef.timeout && classSaveRef.pendingArgs) {
				clearTimeout(classSaveRef.timeout);
				executeAutoSaveClass(classSaveRef.pendingArgs);
			}
			if (kwSaveRef.timeout && kwSaveRef.pendingArgs) {
				clearTimeout(kwSaveRef.timeout);
				executeAutoSaveKeywordGroup(kwSaveRef.pendingArgs);
			}
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	// Input change handlers
	const handleClassChange = (
		clientId: string,
		field: "name" | "description",
		value: string
	): void => {
		const updatedClasses = classes.map((cls) =>
			cls.clientId === clientId ? { ...cls, [field]: value } : cls
		);
		setClasses(updatedClasses);
		setIsModified(true);
	};

	// Auto-save class data with stable ref-based debounce
	const autoSaveClassRef = useRef<{
		timeout: ReturnType<typeof setTimeout> | null;
		pendingArgs: string | null;
	}>({ timeout: null, pendingArgs: null });

	const executeAutoSaveClass = useCallback(
		async (clientId: string) => {
			const updatedClass = classesRef.current.find(
				(cls) => cls.clientId === clientId
			);
			if (!updatedClass) return;
			saveStatus.setSaving(clientId);
			try {
				const response = await mutations.saveClass(updatedClass);
				if (response?.data && !updatedClass.id) {
					const newClientId = String(response.data.id);
					setClasses((prev) =>
						prev.map((cls) =>
							cls.clientId === clientId
								? { ...cls, id: response.data.id, clientId: newClientId }
								: cls
						)
					);
					saveStatus.clearStatus(clientId);
					saveStatus.setSaved(newClientId);
				} else {
					saveStatus.setSaved(clientId);
				}
			} catch (error) {
				console.error("Error saving class data", error);
				saveStatus.setError(clientId);
				mutations.notifyError(error);
			} finally {
				setIsModified(false);
			}
		},
		[mutations, saveStatus]
	);

	const autoSaveClass = useCallback(
		(clientId: string) => {
			const ref = autoSaveClassRef.current;
			if (ref.timeout) clearTimeout(ref.timeout);
			ref.pendingArgs = clientId;
			ref.timeout = setTimeout(() => {
				ref.pendingArgs = null;
				ref.timeout = null;
				executeAutoSaveClass(clientId);
			}, 500);
		},
		[executeAutoSaveClass]
	);

	const handleKeywordChange = (clientId: string, value: string): void => {
		const updatedKeywordGroups = keywordGroups.map((group) =>
			group.clientId === clientId
				? {
						...group,
						musts: value,
					}
				: group
		);
		setKeywordGroups(updatedKeywordGroups);
		setIsModified(true);
	};

	const handleKeywordRegexToggle = async (
		clientId: string,
		checked: boolean
	): Promise<void> => {
		setKeywordGroups((prev) =>
			prev.map((group) =>
				group.clientId === clientId ? { ...group, is_regex: checked } : group
			)
		);
		const group = keywordGroups.find((g) => g.clientId === clientId);
		if (group?.id && group?.musts) {
			try {
				await mutations.saveKeywordConfig({
					...group,
					is_regex: checked,
				});
			} catch (error: any) {
				mutations.notifyError(error);
			}
		}
	};

	// Auto-save for keyword group changes with stable ref-based debounce
	const autoSaveKwRef = useRef<{
		timeout: ReturnType<typeof setTimeout> | null;
		pendingArgs: string | null;
	}>({ timeout: null, pendingArgs: null });

	const executeAutoSaveKeywordGroup = useCallback(
		async (clientId: string) => {
			const updatedGroup = keywordGroupsRef.current.find(
				(group) => group.clientId === clientId
			);
			if (!updatedGroup) return;

			saveStatus.setSaving(clientId);
			try {
				const response = await mutations.saveKeywordConfig(updatedGroup);
				if (updatedGroup.id && updatedGroup.musts === "") {
					saveStatus.clearStatus(clientId);
					setKeywordGroups((prev) =>
						prev.filter((g) => g.clientId !== clientId)
					);
				} else if (response?.data && !updatedGroup.id) {
					const newClientId = String(response.data.id);
					setKeywordGroups((prev) =>
						prev.map((g) =>
							g.clientId === clientId
								? { ...g, id: response.data.id, clientId: newClientId }
								: g
						)
					);
					saveStatus.clearStatus(clientId);
					saveStatus.setSaved(newClientId);
				} else {
					saveStatus.setSaved(clientId);
				}
			} catch (error: any) {
				saveStatus.setError(clientId);
				mutations.notifyError(error);
				console.error("Error submitting class", error);
			} finally {
				setIsModified(false);
			}
		},
		[mutations, saveStatus]
	);

	const autoSaveKeywordGroup = useCallback(
		(clientId: string) => {
			const ref = autoSaveKwRef.current;
			if (ref.timeout) clearTimeout(ref.timeout);
			ref.pendingArgs = clientId;
			ref.timeout = setTimeout(() => {
				ref.pendingArgs = null;
				ref.timeout = null;
				executeAutoSaveKeywordGroup(clientId);
			}, 500);
		},
		[executeAutoSaveKeywordGroup]
	);

	const handleUpdateBasicInfo = async () => {
		setIsBasicInfoSaving(true);
		try {
			await mutations.updateBasicInfo({
				name: classifierName,
				description: classifierDescription,
			});
			setIsBasicModified(false);
			mutations.notifySuccess();
		} catch (error) {
			console.error("Error applying classifier", error);
			mutations.notifyError(error);
		} finally {
			setIsBasicInfoSaving(false);
		}
	};

	const handleAddKeywordGroup = async (classId: number): Promise<void> => {
		const musts = newKeywordMusts[classId]?.trim();
		if (!musts) return;
		const isRegex = newKeywordIsRegex[classId] || false;
		try {
			const response = await mutations.addKeywordConfig({
				class_id: classId,
				musts,
				nots: "",
				is_regex: isRegex,
			});
			if (response?.data) {
				setKeywordGroups((prev) => [
					...prev,
					{ ...response.data, clientId: String(response.data.id) },
				]);
			}
			setNewKeywordMusts((prev) => ({ ...prev, [classId]: "" }));
			setNewKeywordIsRegex((prev) => ({ ...prev, [classId]: false }));
		} catch (error) {
			mutations.notifyError(error);
		}
	};

	const handleRemoveKeywordGroup = async (clientId: string): Promise<void> => {
		try {
			const groupToRemove = keywordGroups.find(
				(group) => group.clientId === clientId
			);
			if (groupToRemove?.id) {
				await mutations.removeKeywordConfig(groupToRemove.id);
			}
			setKeywordGroups((prev) => prev.filter((g) => g.clientId !== clientId));
		} catch (error) {
			console.error("Error removing keyword group", error);
		}
	};

	const handleAddClass = async (): Promise<void> => {
		const name = newClassName.trim();
		if (!name) return;
		try {
			const response = await mutations.addClass({
				name,
				description: newClassDescription.trim(),
			});
			if (response?.data) {
				setClasses((prev) => [
					...prev,
					{ ...response.data, clientId: String(response.data.id) },
				]);
			}
			setNewClassName("");
			setNewClassDescription("");
			mutations.notifySuccess();
		} catch (error) {
			mutations.notifyError(error);
		}
	};

	const handleRemoveClass = async (clientId: string): Promise<void> => {
		try {
			const classToRemove = classes.find((cls) => cls.clientId === clientId);
			if (!classToRemove) return;
			if (classToRemove.id) {
				await mutations.removeClass(classToRemove.id);
			}
			setClasses((prev) => prev.filter((cls) => cls.clientId !== clientId));
			setKeywordGroups((prev) =>
				prev.filter((g) => g.class_id !== classToRemove.id)
			);
		} catch (error) {
			mutations.notifyError(error);
			console.error("Error removing class:", error);
		}
	};

	const handleExportCsv = async () => {
		try {
			await mutations.exportCsv();
			mutations.notifySuccess("classifiers.success.export");
		} catch (error) {
			mutations.notifyError(error);
		}
	};

	return (
		<div className="p-8 bg-white min-h-screen">
			<ClassifierViewBreadcrumb
				record={classifier}
				projectid={projectid as string}
			/>
			<h1 className="text-2xl font-semibold">
				{translate("classifiers.types.keyword_match.edit")}
			</h1>
			<p className="mb-4">
				{translate("classifiers.types.keyword_match.edit_description")}
			</p>

			<Space h="md" />
			<div>
				<Divider
					my="sm"
					label={translate(
						"classifiers.types.keyword_match.view.accordion.basic_setup"
					)}
				/>
				<TextInput
					label={translate("projects.fields.name")}
					placeholder={translate("classifiers.fields.name_placeholder")}
					value={classifierName}
					onChange={(e) => {
						setIsBasicModified(true);
						setClassifierName(e.target.value);
					}}
					required
				/>
				<Space h="sm" />
				<TextInput
					label={translate("projects.fields.description")}
					placeholder={translate("classifiers.fields.description_placeholder")}
					value={classifierDescription}
					onChange={(e) => {
						setIsBasicModified(true);
						setClassifierDescription(e.target.value);
					}}
					required
				/>
				<Space h="sm" />
				<div className="flex justify-end">
					<Button
						leftIcon={<IconCheck size={16} />}
						mt="sm"
						onClick={handleUpdateBasicInfo}
						loading={isBasicInfoSaving}
						disabled={isBasicInfoSaving}
					>
						{translate("buttons.update_basic_info")}
					</Button>
				</div>
			</div>
			<Space h="lg" />

			{/* Classes Section */}
			<Divider
				my="sm"
				label={translate(
					"classifiers.types.keyword_match.view.accordion.configuration"
				)}
			/>
			<p className="text-sm text-gray-500 mb-2">
				{translate("classifiers.import_export_recommendation")}
			</p>
			<div className="flex gap-2 mb-4">
				<Button
					leftIcon={<IconDownload size={16} />}
					variant="outline"
					onClick={handleExportCsv}
				>
					{translate("classifiers.export_csv")}
				</Button>
				<Button
					leftIcon={<IconUpload size={16} />}
					variant="outline"
					onClick={() => setImportOpened(true)}
				>
					{translate("classifiers.import_csv")}
				</Button>
			</div>
			<ClassifierImportCsvModal
				opened={importOpened}
				setOpened={setImportOpened}
				projectId={projectid as string}
				classifierId={id as string}
				onSuccess={() => fetchData()}
			/>
			<Table highlightOnHover withBorder>
				<thead>
					<tr>
						<th>{translate("classifiers.fields.class_name")}</th>
						<th>{translate("projects.fields.description")}</th>
						<th className="text-center" style={{ width: "120px" }}>
							{translate("classifiers.fields.keyword_count")}
						</th>
						<th className="text-center" style={{ width: "100px" }}>
							{translate("table.actions")}
						</th>
					</tr>
				</thead>
				<tbody>
					{classes?.map((classItem) => {
						const classKey = classItem.id!;
						const classKeywordGroups = keywordGroups?.filter(
							(group) => group.class_id === classItem.id
						);
						return (
							<Fragment key={classItem.clientId}>
								<tr>
									<td className="align-baseline">
										<div className="flex items-center">
											<TextInput
												placeholder={translate(
													"classifiers.fields.class_name_placeholder"
												)}
												value={classItem.name}
												onChange={(event: ChangeEvent<HTMLInputElement>) => {
													handleClassChange(
														classItem.clientId,
														"name",
														event.target.value
													);
													setIsModified(true);
												}}
												onBlur={() => {
													autoSaveClass(classItem.clientId);
												}}
												className="flex-1"
											/>
											{saveStatus.getStatus(classItem.clientId) ===
												"saving" && (
												<span className="inline-flex items-center text-xs text-gray-500 ml-2">
													<Loader size={12} className="mr-1" />
												</span>
											)}
											{saveStatus.getStatus(classItem.clientId) === "saved" && (
												<span className="inline-flex items-center text-xs text-green-600 ml-2">
													<IconCheck size={12} />
												</span>
											)}
											{saveStatus.getStatus(classItem.clientId) === "error" && (
												<span className="inline-flex items-center text-xs text-red-600 ml-2">
													<IconExclamationMark size={12} />
												</span>
											)}
										</div>
									</td>
									<td className="align-baseline">
										<TextInput
											placeholder={translate(
												"classifiers.fields.class_description_placeholder"
											)}
											value={classItem.description}
											onChange={(event: ChangeEvent<HTMLInputElement>) => {
												handleClassChange(
													classItem.clientId,
													"description",
													event.target.value
												);
												setIsModified(true);
											}}
											onBlur={() => {
												autoSaveClass(classItem.clientId);
											}}
										/>
									</td>
									<td className="align-baseline text-center">
										{classKeywordGroups.length}
									</td>
									<td className="align-baseline">
										<div className="flex gap-1 items-center justify-center">
											<Tooltip
												label={translate(
													"classifiers.actions.tooltips.delete_class"
												)}
											>
												<ActionIcon
													color="red"
													variant="light"
													onClick={() => handleRemoveClass(classItem.clientId)}
												>
													<IconTrash size={16} />
												</ActionIcon>
											</Tooltip>
											<ActionIcon
												color="dark"
												variant="light"
												onClick={() => toggleRow(classItem.clientId)}
											>
												{openRows[classItem.clientId] ? (
													<IconChevronUp size={16} />
												) : (
													<IconChevronDown size={16} />
												)}
											</ActionIcon>
										</div>
									</td>
								</tr>
								{openRows[classItem.clientId] && (
									<KeywordTable
										classClientId={classItem.clientId}
										classSaveStatus={saveStatus.getStatus(classItem.clientId)}
										classKey={classKey}
										keywordGroups={classKeywordGroups}
										newMustsValue={newKeywordMusts[classKey] || ""}
										newIsRegexValue={newKeywordIsRegex[classKey] || false}
										translate={translate}
										getSaveStatus={saveStatus.getStatus}
										onMustsChange={(key, value) =>
											setNewKeywordMusts((prev) => ({
												...prev,
												[key]: value,
											}))
										}
										onIsRegexChange={(key, checked) =>
											setNewKeywordIsRegex((prev) => ({
												...prev,
												[key]: checked,
											}))
										}
										onAdd={handleAddKeywordGroup}
										onShowRow={showRow}
										onKeywordChange={handleKeywordChange}
										onKeywordSave={autoSaveKeywordGroup}
										onRegexToggle={handleKeywordRegexToggle}
										onRemove={handleRemoveKeywordGroup}
										onModified={() => setIsModified(true)}
									/>
								)}
							</Fragment>
						);
					})}
					<tr>
						<td className="align-baseline">
							<TextInput
								placeholder={translate(
									"classifiers.fields.class_name_placeholder"
								)}
								value={newClassName}
								onChange={(e: ChangeEvent<HTMLInputElement>) =>
									setNewClassName(e.target.value)
								}
							/>
						</td>
						<td className="align-baseline">
							<TextInput
								placeholder={translate(
									"classifiers.fields.class_description_placeholder"
								)}
								value={newClassDescription}
								onChange={(e: ChangeEvent<HTMLInputElement>) =>
									setNewClassDescription(e.target.value)
								}
							/>
						</td>
						<td></td>
						<td className="align-baseline">
							<div className="flex justify-center">
								<Button
									leftIcon={<IconPlus size={16} />}
									variant="subtle"
									onClick={handleAddClass}
									disabled={!newClassName.trim()}
								>
									{translate("buttons.add_class")}
								</Button>
							</div>
						</td>
					</tr>
				</tbody>
			</Table>

			<Space h="lg" />
			<div className="flex justify-end gap-2 w-full">
				<Button
					mt="sm"
					disabled={!classifierName}
					onClick={() => {
						if (classifier)
							navigateWithConfirmation(
								`/projects/${projectid}/classifiers/${classifier.type}/${classifier.id}`
							);
					}}
				>
					{translate("classifiers.buttons.finish")}
				</Button>
			</div>
		</div>
	);
};

export default EditKeywordClassifier;
