"use client";

import {
	TextInput,
	Button,
	Table,
	Tooltip,
	ActionIcon,
	Space,
	Divider,
	Group,
	ScrollArea,
	Text,
} from "@mantine/core";
import {
	IconTrash,
	IconPlus,
	IconCheck,
	IconExternalLink,
} from "@tabler/icons-react";
import { useState, useEffect, ChangeEvent, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslate } from "@refinedev/core";
import { classifierService } from "src/services";
import { showNotification } from "@mantine/notifications";
import ClassifierViewBreadcrumb from "@components/breadcrumbs/classifierView";
import PaginationComponent from "@components/table/pagination";
import ClassifyAuthorModal from "@components/modals/manual-post-author";
import { getAuthorProfileLink } from "src/utils";
import { Author, ClassData } from "../../model";

const EditKeywordClassifier: React.FC = () => {
	const translate = useTranslate();
	const router = useRouter();
	const { projectid, id } = useParams();
	// State to manage classes and keyword groups
	const [classifierName, setClassifierName] = useState("");
	const [classifierDescription, setClassifierDescription] = useState("");
	const [classifier, setClassifier] = useState<any>();
	const [classes, setClasses] = useState<ClassData[]>([]);
	const [authors, setAuthors] = useState<Author[]>([]);
	const [selectedAuthor, setSelectedAuthor] = useState<Author | null>(null);
	const [authorIdx, setAuthorIdx] = useState<number | null>(null);
	const [isModalOpen, setModalOpen] = useState(false);
	const [isModified, setIsModified] = useState<boolean>(false);
	const [isBasicModified, setIsBasicModified] = useState<boolean>(false);
	const [refetch, setRefetch] = useState<boolean>(true);
	const [totalAuthors, setTotalAuthors] = useState(0);
	const [activePage, setActivePage] = useState(1);

	const authorsPerPage = 10; // Number of authors per page

	const navigateWithConfirmation = (url: string) => {
		if (isModified) {
			const confirmed = window.confirm(
				translate("notifications.unsaved_changes")
			);
			if (confirmed) {
				router.push(url); // Proceed with the navigation if confirmed
			}
		} else {
			router.push(url); // Directly navigate if no unsaved changes
		}
	};

	// Fetch initial data on mount
	const fetchAuthors = useCallback(
		async (page: number) => {
			const start = (page - 1) * authorsPerPage;
			const end = start + authorsPerPage;
			try {
				const authorsResponse = await classifierService.getManualPostAuthors({
					project_id: projectid as string,
					classifier_id: id as string,
					params: { start, end },
				});
				setAuthors(authorsResponse?.data?.authors);
				setTotalAuthors(authorsResponse?.data?.meta?.total_count);
			} catch (error) {
				console.error("Failed to fetch authors:", error);
			}
		},
		[id, projectid, setAuthors]
	);

	useEffect(() => {
		fetchAuthors(activePage);
	}, [activePage, fetchAuthors]);
	const fetchData = useCallback(async () => {
		try {
			const response = await classifierService.getClassifierData({
				project_id: projectid as string,
				classifier_id: id as string,
			});
			fetchAuthors(activePage);

			const { data } = response;
			setClassifier(data);
			setClassifierName(data?.name);
			setClassifierDescription(data?.description);
			// Set classes and authors from API response
			setClasses(data.intermediatory_classes);
			setRefetch(false);
		} catch (error) {
			console.error("Error fetching classifier data", error);
		}
	}, [id, projectid, activePage, fetchAuthors]);

	useEffect(() => {
		if (id && projectid && refetch) {
			fetchData();
		}

		// Warn user on exit without saving
		window.onbeforeunload = isModified || isBasicModified ? () => true : null;

		return () => {
			window.onbeforeunload = null;
		};
	}, [isModified, isBasicModified, id, projectid, fetchData, refetch]);

	// Input change handlers
	const handleClassChange = (
		index: number,
		field: "name" | "description",
		value: string
	): void => {
		const updatedClasses = classes.map((cls, i) =>
			i === index ? { ...cls, [field]: value } : cls
		);
		setClasses(updatedClasses);
		setIsModified(true);
	};

	const handleUpdateBasicInfo = async () => {
		try {
			await classifierService.updateClassifierBasicData(
				{
					project_id: projectid,
					classifier_id: id,
				},
				{
					name: classifierName,
					description: classifierDescription,
				}
			);
			setIsBasicModified(false);
			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.success"),
			});
		} catch (error) {
			console.error("Error applying classifier", error);
		}
	};

	const handleAddClass = (): void => {
		setClasses([
			...classes,
			{ tempId: Math.random(), name: "", description: "" },
		]);
	};

	const handleRemoveClass = async (index: number): Promise<void> => {
		const classToRemove = classes[index];
		if (classToRemove?.id) {
			try {
				await classifierService.removeClassifierClassData({
					project_id: projectid,
					classifier_id: id,
					class_id: classToRemove.id,
				});
				setRefetch(true);
			} catch (error) {
				console.error("Error removing class", error);
			}
		} else {
			try {
				setClasses(classes.filter((_, i) => i !== index));
			} catch (error: any) {
				showNotification({
					title: translate("status.error"),
					color: "red",
					message: error?.response?.data?.message || "An Error Occured",
				});
				console.error("Error removing class", error);
			}
		}
	};

	const handleSubmitClass = async (classIndex: number): Promise<void> => {
		const classToAdd = classes[classIndex];
		try {
			if (classToAdd?.id) {
				await classifierService.updateClassifierClassData(
					{
						project_id: projectid,
						classifier_id: id,
						class_id: classToAdd.id,
					},
					{
						name: classToAdd.name,
						description: classToAdd.description,
					}
				);
			} else if (classToAdd?.tempId) {
				await classifierService.createClassifierClassData(
					{
						project_id: projectid,
						classifier_id: id,
					},
					{
						name: classToAdd.name,
						description: classToAdd.description,
					}
				);
			}
			setRefetch(true);
		} catch (error: any) {
			showNotification({
				title: "Error",
				color: "red",
				message: error?.response?.data?.message || "An Error Occured",
			});
			console.error("Error creating/updating class", error);
		}
	};

	const handleSaveAll = async (): Promise<void> => {
		try {
			classes.map(async (_, idx) => await handleSubmitClass(idx));
			setIsModified(false);
			showNotification({
				title: translate("status.success"),
				message: translate("classifiers.success.success"),
			});
		} catch (error: any) {
			showNotification({
				title: translate("status.error"),
				color: "red",
				message: error?.response?.data?.message || "An Error Occured",
			});
			console.error("Error creating/updating class", error);
		}
	};

	const openClassifyModal = (author: Author, idx: number) => {
		setAuthorIdx(idx);
		setSelectedAuthor(author);
		setModalOpen(true);
	};

	const closeModal = () => {
		fetchData();
		setAuthorIdx(null);
		setSelectedAuthor(null);
		setModalOpen(false);
	};

	const goToNext = (index: number) => {
		const newSelection = authors.find((_, idx) => idx === index + 1);
		if (newSelection) {
			setAuthorIdx(index + 1);
			setSelectedAuthor(newSelection);
		} else {
			setSelectedAuthor(null);
			setModalOpen(false);
		}
	};

	return (
		<div className="p-8 bg-white min-h-screen">
			<ClassifierViewBreadcrumb
				record={classifier}
				projectid={projectid as string}
			/>
			<h1 className="text-2xl font-semibold">
				{translate("classifiers.types.manual_post_authors.edit")}
			</h1>
			<p className="mb-4">
				{translate("classifiers.types.manual_post_authors.edit_description")}
			</p>

			<Space h="md" />
			<div>
				<Divider
					my="sm"
					label={translate(
						"classifiers.types.manual_post_authors.view.accordion.basic_setup"
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
					"classifiers.types.manual_post_authors.view.accordion.class_configuration"
				)}
			/>
			<Table highlightOnHover withBorder>
				<thead>
					<tr>
						<th>{translate("classifiers.fields.class_name")}</th>
						<th>{translate("projects.fields.description")}</th>
						<th>{translate("table.actions")}</th>
					</tr>
				</thead>
				<tbody>
					{classes?.map((classItem, classIndex) => (
						<tr key={classIndex}>
							<td className="align-baseline">
								<TextInput
									placeholder={translate(
										"classifiers.fields.class_name_placeholder"
									)}
									value={classItem.name}
									onChange={(event: ChangeEvent<HTMLInputElement>) =>
										handleClassChange(classIndex, "name", event.target.value)
									}
								/>
							</td>
							<td className="align-baseline">
								<TextInput
									placeholder={translate(
										"classifiers.fields.class_description_placeholder"
									)}
									value={classItem.description}
									onChange={(event: ChangeEvent<HTMLInputElement>) =>
										handleClassChange(
											classIndex,
											"description",
											event.target.value
										)
									}
								/>
							</td>
							<td className="align-baseline">
								<div className="w-full h-full flex gap-1 items-center justify-center">
									<Tooltip
										label={translate(
											"classifiers.actions.tooltips.delete_class"
										)}
									>
										<ActionIcon
											color="red"
											variant="light"
											onClick={() => handleRemoveClass(classIndex)}
										>
											<IconTrash size={16} />
										</ActionIcon>
									</Tooltip>
								</div>
							</td>
						</tr>
					))}
				</tbody>
				<div className="flex gap-2 m-2 w-full">
					<Button
						leftIcon={<IconPlus size={16} />}
						variant="subtle"
						onClick={handleAddClass}
					>
						{translate("buttons.add_class")}
					</Button>
					<Button rightIcon={<IconCheck size={16} />} onClick={handleSaveAll}>
						{translate("buttons.save_all")}
					</Button>
				</div>
			</Table>
			<Space h="lg" />

			{/* Authors Section */}
			<Divider
				my="sm"
				label={translate(
					"classifiers.types.manual_post_authors.view.accordion.author_configuration"
				)}
			/>
			<Text size="sm" color="dimmed" className="mb-4">
				{translate("classifiers.types.manual_post_authors.author_count")}
				{totalAuthors}
			</Text>
			<ScrollArea>
				<Table highlightOnHover withBorder>
					<thead>
						<tr>
							<th>
								{translate(
									"classifiers.types.manual_post_authors.fields.classes"
								)}
							</th>
							<th>
								{translate(
									"classifiers.types.manual_post_authors.fields.author_name"
								)}
							</th>
							<th>
								{translate(
									"classifiers.types.manual_post_authors.fields.no_of_posts"
								)}
							</th>
							<th>
								{translate(
									"classifiers.types.manual_post_authors.fields.author_platform"
								)}
							</th>
							<th>
								{translate(
									"classifiers.types.manual_post_authors.fields.author_anon_id"
								)}
							</th>
							<th>{translate("table.actions")}</th>
						</tr>
					</thead>
					<tbody>
						{authors.map((author, authorIndex) => (
							<tr key={author.phoenix_platform_message_author_id}>
								<td>
									<div className="flex flex-wrap">
										{author.intermediatory_author_classes.map((cls) => (
											<span
												key={cls.class_id}
												className="mr-2 mb-2 px-2 py-1 bg-gray-200 rounded text-sm sm:text-base"
											>
												{cls.class_name}
											</span>
										))}
									</div>
								</td>
								<td>
									{author.pi_platform_message_author_name}
									<Button
										component="a"
										href={getAuthorProfileLink(author)}
										target="_blank"
										rel="noopener noreferrer"
										p={0}
										variant="subtle"
									>
										<IconExternalLink size={16} />
									</Button>
								</td>
								<td>{author.post_count}</td>
								<td className="capitalize">{author.platform}</td>
								<td>{author.pi_platform_message_author_id}</td>
								<td>
									<Group spacing="xs">
										<Button
											size="xs"
											variant="default"
											onClick={() => openClassifyModal(author, authorIndex)}
										>
											{translate("buttons.edit")}
										</Button>
									</Group>
								</td>
							</tr>
						))}
					</tbody>
				</Table>
			</ScrollArea>
			{/* Wrapper for pagination */}
			<div className="flex justify-end mt-4 w-full">
				<PaginationComponent
					pages={Math.ceil(totalAuthors / authorsPerPage)}
					_activeIndex={activePage}
					_setActiveIndex={setActivePage}
				/>
			</div>

			<Space h="lg" />
			<div className="flex justify-end gap-2 w-full">
				<Button
					mt="sm"
					// fullWidth
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
			{/* Classify Author Modal */}
			{selectedAuthor && authorIdx?.toString && (
				<ClassifyAuthorModal
					authorIdx={authorIdx}
					authorsCount={authors.length}
					goToNext={goToNext}
					isOpen={isModalOpen}
					onClose={closeModal}
					author={selectedAuthor}
					projectId={projectid as string}
					classifierId={id as string}
					availableClasses={(classes || [])
						.filter((c) => c?.id && c?.name)
						.map((c) => ({
							value: c?.id?.toString() || "",
							label: c.name,
						}))}
				/>
			)}
		</div>
	);
};

export default EditKeywordClassifier;
