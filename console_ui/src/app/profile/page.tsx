"use client";

import React, { useEffect, useState } from "react";
import {
	Paper,
	Button,
	Container,
	Text,
	TextInput,
	Divider,
	Accordion,
	Badge,
	Group,
} from "@mantine/core";
import { useGetIdentity, useTranslate } from "@refinedev/core";
import { useForm } from "@refinedev/mantine";
import { UserInfo } from "src/interfaces/user";
import { normaliseErrorMessage, toReadableDate } from "src/utils";
import { userService } from "src/services";
import { showNotification } from "@mantine/notifications";

interface AccordionLabelProps {
	label: string;
	description: string;
}

function AccordionLabel({ label, description }: AccordionLabelProps) {
	return (
		<Group noWrap>
			<div>
				<h2 className="text-xl font-semibold my-0">{label}</h2>
				<Text size="sm" color="dimmed" weight={400}>
					{description}
				</Text>
			</div>
		</Group>
	);
}

const ProfilePage: React.FC = () => {
	const translate = useTranslate();
	const { data: user } = useGetIdentity<UserInfo>();
	const { getInputProps, values, reset, setFieldValue } = useForm({
		initialValues: {
			display_name: user?.display_name || "",
		},
		validate: {},
	});

	const [isSaving, setIsSaving] = useState(false);
	const [savedDisplayName, setSavedDisplayName] = useState<string>(
		user?.display_name || ""
	);

	useEffect(() => {
		if (user?.display_name) {
			setFieldValue("display_name", user?.display_name);
			setSavedDisplayName(user.display_name); // Track the saved display name
		}
	}, [user?.display_name, setFieldValue]);

	const handleUpdateBasicInfo = async () => {
		if (user?.id && values.display_name !== savedDisplayName) {
			setIsSaving(true);
			try {
				await userService.updateUser(user.id, {
					display_name: values.display_name,
					app_role: "admin",
				});
				setSavedDisplayName(values.display_name); // Update the saved display name after a successful save
				showNotification({
					title: translate("status.success"),
					message: translate("status.success"),
				});
			} catch (err: any) {
				showNotification({
					title: translate("status.error"),
					color: "red",
					message: normaliseErrorMessage(err, translate),
				});
			} finally {
				setIsSaving(false);
			}
		}
	};

	const handleCancel = () => {
		reset();
	};

	return (
		<Paper className="h-[100vh]" shadow="sm" radius="md" p="lg">
			<div className="flex flex-col p-4">
				<h2 className="text-xxl font-bold capitalize my-0">
					{savedDisplayName}
				</h2>
				<Badge className="w-max">Admin</Badge>
				<Text size="sm" className="mt-4">
					{translate("pages.profile.email")}: <strong>{user?.email}</strong>
				</Text>
				{user?.created_at && (
					<Text size="sm">
						{translate("pages.profile.created_at")}:{" "}
						<strong>{toReadableDate(user.created_at)}</strong>
					</Text>
				)}
			</div>
			<Divider my="sm" />
			<Accordion
				styles={{
					item: {
						"&[data-active]": {
							backgroundColor: "none",
						},
					},
				}}
			>
				<Accordion.Item value="profile-settings">
					<Accordion.Control>
						<AccordionLabel
							label={translate("pages.profile.settings.title")}
							description={translate("pages.profile.settings.description")}
						/>
					</Accordion.Control>
					<Accordion.Panel>
						<Container className="mx-0 flex flex-col my-4">
							<div className="flex flex-col">
								<TextInput
									mt="sm"
									withAsterisk
									label={translate("pages.profile.fields.name")}
									{...getInputProps("display_name")}
								/>
							</div>
							<div className="flex gap-4 items-center mt-4">
								<Button
									onClick={handleUpdateBasicInfo}
									disabled={
										!values.display_name ||
										values.display_name === savedDisplayName ||
										isSaving
									}
									loading={isSaving}
								>
									{translate("buttons.save")}
								</Button>
								<Button variant="outline" onClick={handleCancel}>
									{translate("buttons.cancel")}
								</Button>
							</div>
						</Container>
					</Accordion.Panel>
				</Accordion.Item>
			</Accordion>
		</Paper>
	);
};

export default ProfilePage;
