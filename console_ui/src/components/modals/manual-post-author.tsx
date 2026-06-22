import React, { useCallback, useEffect, useState } from "react";
import { Modal, Button, MultiSelect, Text, Group, Loader } from "@mantine/core";
import { showNotification } from "@mantine/notifications";
import { Author } from "@pages/projects/[projectid]/classifiers/manual_post_authors/model";
import { classifierService } from "src/services";
import { useTranslate } from "@refinedev/core";
import { getAuthorProfileLink } from "src/utils";
import { IconExternalLink } from "@tabler/icons-react";

interface ClassifyAuthorModalProps {
	authorIdx: number;
	authorsCount: number;
	goToNext: (idx: number) => void;
	isOpen: boolean;
	onClose: () => void;
	author: Author;
	projectId: string;
	classifierId: string;
	availableClasses: Array<{ value: string; label: string }>;
}

const ClassifyAuthorModal: React.FC<ClassifyAuthorModalProps> = ({
	authorIdx,
	authorsCount,
	goToNext,
	isOpen,
	onClose,
	author,
	projectId,
	classifierId,
	availableClasses,
}) => {
	const translate = useTranslate();
	const [isLoading, setIsLoading] = useState(false);
	const [authorData, setAuthorData] = useState(author);
	const [selectedClasses, setSelectedClasses] = useState(
		authorData?.intermediatory_author_classes.map((c) => c.class_id.toString())
	);

	// Fetch the latest author data
	const fetchAuthor = useCallback(async () => {
		try {
			const authorsResponse = await classifierService.getManualPostAuthorById({
				project_id: projectId,
				classifier_id: classifierId,
				id: author.phoenix_platform_message_author_id,
			});
			setAuthorData(authorsResponse?.data);
		} catch (error) {
			console.error("Failed to fetch authors:", error);
		}
	}, [classifierId, author, projectId]);

	// Mutation to add class to the author
	const addClassMutation = async (classId: string) => {
		setIsLoading(true);
		try {
			await classifierService.addClassToManualPostAuthorClassifier(
				{
					project_id: projectId,
					classifier_id: classifierId,
				},
				{
					class_id: Number(classId),
					phoenix_platform_message_author_id:
						author.phoenix_platform_message_author_id,
				}
			);
			// Re-fetch author data after adding the class to get the correct class author ID
			await fetchAuthor();
		} catch (error: any) {
			showNotification({
				title: "Error",
				color: "red",
				message: error?.response?.data?.message || "Failed to add class",
			});
		} finally {
			setIsLoading(false);
		}
	};

	// Mutation to remove class from the author
	const removeClassMutation = async (classId: string) => {
		setIsLoading(true);
		try {
			// Find the class author to remove
			const classAuthor = authorData.intermediatory_author_classes.find(
				(item) => item.class_id === Number(classId)
			);

			// If the class is found and it has an ID, delete it
			if (classAuthor?.id) {
				await classifierService.removeClassToManualPostAuthorClassifier({
					project_id: projectId,
					classifier_id: classifierId,
					classified_post_author_id: classAuthor.id,
				});
				// Re-fetch author data after removing the class
				await fetchAuthor();
			}
		} catch (error: any) {
			showNotification({
				title: "Error",
				color: "red",
				message: error?.response?.data?.message || "Failed to remove class",
			});
		} finally {
			setIsLoading(false);
		}
	};

	// Handle class selection changes
	const handleClassChange = (newSelectedClasses: string[]) => {
		// Find added classes
		const addedClasses = newSelectedClasses.filter(
			(id) => !selectedClasses.includes(id)
		);
		// Find removed classes
		const removedClasses = selectedClasses.filter(
			(id) => !newSelectedClasses.includes(id)
		);

		// Add newly selected classes
		addedClasses.forEach(async (classId) => {
			await addClassMutation(classId);
		});

		// Remove unselected classes
		removedClasses.forEach(async (classId) => {
			await removeClassMutation(classId);
		});

		// Update selected classes in state
		setSelectedClasses(newSelectedClasses);
	};

	useEffect(() => {
		setAuthorData(author);
	}, [author]);

	useEffect(() => {
		// Ensure the selected classes state is updated whenever authorData changes
		setSelectedClasses(
			authorData.intermediatory_author_classes.map((c) => c.class_id.toString())
		);
	}, [authorData]);

	return (
		<Modal opened={isOpen} onClose={onClose} size="lg">
			<div className="font-medium flex flex-col px-8 pb-8">
				<Text size="xl" weight={500} className="mb-2">
					{translate("classifiers.types.manual_post_authors.author_edit.title")}
				</Text>
				<Text size="sm" color="dimmed" className="mb-4">
					{translate(
						"classifiers.types.manual_post_authors.author_edit.instruction"
					)}
				</Text>

				<Text size="sm" color="dimmed" className="mb-4">
					{translate("classifiers.types.manual_post_authors.author_edit.count")}
					{` ${authorIdx + 1} of ${authorsCount}`}
				</Text>
				<div>
					<div className="w-full flex mb-5 p-1">
						<div className="w-1/2 flex flex-col">
							<div className="flex items-center">
								<Text className="font-medium text-lg capitalize">
									{authorData.pi_platform_message_author_name}
								</Text>
								&nbsp;
								<Button
									component="a"
									href={getAuthorProfileLink(author)}
									target="_blank"
									rel="noopener noreferrer"
									p={0}
									variant="subtle"
								>
									<IconExternalLink size={20} />
								</Button>
							</div>
							<Text className="text-base text-neutral-500 font-normal">
								{translate(
									"classifiers.types.manual_post_authors.fields.author_name"
								)}
							</Text>
						</div>
					</div>
					<div className="w-full flex mb-5 p-1">
						<div className="w-1/2 flex flex-col">
							<Text className="font-medium text-lg capitalize">
								{authorData.post_count}
							</Text>
							<Text className="text-base text-neutral-500 font-normal">
								{translate(
									"classifiers.types.manual_post_authors.fields.no_of_posts"
								)}
							</Text>
						</div>
						<div className="w-1/2 flex flex-col">
							<Text className="font-medium capitalize text-lg">
								{authorData.platform}
							</Text>
							<Text className="text-base text-neutral-500 font-normal">
								{translate(
									"classifiers.types.manual_post_authors.fields.author_platform"
								)}
							</Text>
						</div>
					</div>
					<div className="w-full flex mb-5 p-1">
						<div className="w-1/2 flex flex-col">
							<Text className="font-medium text-lg">
								{authorData.pi_platform_message_author_id}
							</Text>
							<Text className="text-base text-neutral-500 font-normal">
								{translate(
									"classifiers.types.manual_post_authors.fields.author_anon_id"
								)}
							</Text>
						</div>
					</div>
					<MultiSelect
						label={translate(
							"classifiers.types.manual_post_authors.fields.classes"
						)}
						placeholder="Select classes"
						data={availableClasses}
						value={selectedClasses}
						onChange={handleClassChange}
						searchable
						clearable
					/>
				</div>

				{isLoading && (
					<Group position="center" mt="md">
						<Loader size="sm" />
						<Text>
							{translate(
								"classifiers.types.manual_post_authors.author_edit.processing"
							)}
							...
						</Text>
					</Group>
				)}

				<Group position="right" mt="lg">
					<Button variant="outline" onClick={onClose}>
						{translate(
							"classifiers.types.manual_post_authors.author_edit.go_back_to_list"
						)}
					</Button>
					<Button
						onClick={() => goToNext(authorIdx)}
						disabled={isLoading || authorIdx + 1 >= authorsCount}
					>
						{translate(
							"classifiers.types.manual_post_authors.author_edit.go_to_next"
						)}
					</Button>
				</Group>
			</div>
		</Modal>
	);
};

export default ClassifyAuthorModal;
