"use client";

import React, {
	ChangeEvent,
	KeyboardEvent,
	ReactNode,
	useEffect,
	useState,
} from "react";
import {
	Button,
	Text,
	TextInput,
	Group,
	Textarea,
	Box,
	Divider,
} from "@mantine/core";
import {
	IconCircleCheck,
	IconExternalLink,
	IconPencil,
	IconTrash,
} from "@tabler/icons-react";
import { useTranslate } from "@refinedev/core";
import { templateString } from "src/utils/constants";

interface Props {
	error?: string;
	label?: ReactNode;
	placeholder: string;
	data: string[];
	setData: React.Dispatch<React.SetStateAction<string[]>>;
	template_url_for_input?: string;
	link?: boolean;
	split_regex: RegExp;
}

const GatherInputs: React.FC<Props> = ({
	error,
	label,
	placeholder,
	data,
	setData,
	template_url_for_input,
	link = true,
	split_regex,
}) => {
	const translate = useTranslate();
	const [inputValue, setInputValue] = useState<string>("");
	const [editIndex, setEditIndex] = useState<number | null>(null);
	const [editedValue, setEditedValue] = useState<string>("");

	const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
		setInputValue(e.target.value);
	};

	const handleAddInput = () => {
		if (inputValue.trim() !== "") {
			const inputs = inputValue
				.split(split_regex) // Split by commas and spaces
				.map((input) => input.trim())
				.filter((input) => input !== "");

			// Create a Set to store unique inputs
			const uniqueInputs = new Set([...data, ...inputs]);

			// Convert Set back to an array
			setData(Array.from(uniqueInputs));

			setInputValue("");
		}
	};

	const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter") {
			handleAddInput();
		}
	};

	const handleRemoveInput = (input: string) => {
		setData((prevInputs) => prevInputs.filter((e) => e !== input));
	};

	const handleEditItem = (index: number, newValue: string) => {
		setEditedValue(newValue);
		setEditIndex(index);
	};

	const handleSaveItem = () => {
		if (editedValue.trim() !== "") {
			setData((prevItems) =>
				prevItems.map((item, index) =>
					index === editIndex ? editedValue : item
				)
			);
		}
		setEditIndex(null);
	};

	return (
		<div>
			<Textarea
				mt="lg"
				mb="sm"
				label={label}
				value={inputValue}
				onChange={handleInputChange}
				onKeyDown={handleKeyDown}
				onBlur={handleAddInput}
				placeholder={placeholder}
				error={error}
			/>
			{data.length > 0 && (
				<Box
					py={16}
					sx={{
						border: "1px solid rgba(0, 0, 0, 0.1)",
						maxWidth: "fit-content",
					}}
				>
					{data.map((item: string, idx: number) => (
						<div key={item} className="pt-2">
							{editIndex === idx ? (
								<TextInput
									mx={16}
									label={translate("gathers.fields.input.edit_input_label")}
									value={editedValue}
									onChange={(e) => setEditedValue(e.currentTarget.value)}
									rightSection={
										<IconCircleCheck
											color="green"
											className="cursor-pointer"
											onClick={handleSaveItem}
										/>
									}
									placeholder={translate(
										"gathers.fields.input.edit_input_label"
									)}
									autoFocus
								/>
							) : (
								<div className="flex items-center justify-between gap-10 px-4">
									<Text>{item}</Text>
									<Group>
										<Button
											p={0}
											variant="subtle"
											onClick={() => handleEditItem(idx, item)}
										>
											<IconPencil color="black" size={16} />
										</Button>
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
										<Button
											p={0}
											color="red"
											variant="subtle"
											onClick={() => handleRemoveInput(item)}
										>
											<IconTrash
												size={16}
												color="red"
												className="cursor-pointer"
											/>
										</Button>
									</Group>
								</div>
							)}
							{idx < data.length - 1 && <Divider className="mt-2" />}
						</div>
					))}
				</Box>
			)}
		</div>
	);
};

export default GatherInputs;
