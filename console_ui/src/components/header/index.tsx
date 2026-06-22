"use client";

import {
	ActionIcon,
	Avatar,
	Flex,
	Group,
	Header as MantineHeader,
	Menu,
	Sx,
	Title,
	useMantineColorScheme,
	useMantineTheme,
} from "@mantine/core";
import { useGetIdentity, useGetLocale, useSetLocale } from "@refinedev/core";
import {
	HamburgerMenu,
	RefineThemedLayoutHeaderProps as RefineThemedLayoutV2HeaderProps,
} from "@refinedev/mantine";
import { IconLanguage, IconMoonStars, IconSun } from "@tabler/icons-react";
import React from "react";
import { useTranslation } from "react-i18next";

type IUser = {
	id: number;
	name: string;
	avatar: string;
};

const Header: React.FC<RefineThemedLayoutV2HeaderProps> = ({ sticky }) => {
	const { i18n } = useTranslation();
	const locale = useGetLocale();
	const changeLanguage = useSetLocale();
	const currentLocale = locale();

	const { data: user } = useGetIdentity<IUser>();

	const theme = useMantineTheme();

	const { colorScheme, toggleColorScheme } = useMantineColorScheme();
	const dark = colorScheme === "dark";

	const borderColor = dark ? theme.colors.dark[6] : theme.colors.gray[2];

	let stickyStyles: Sx = {};
	if (sticky) {
		stickyStyles = {
			position: "sticky",
			top: 0,
			zIndex: 1,
		};
	}

	return (
		<MantineHeader
			zIndex={199}
			height={64}
			py={6}
			px="sm"
			sx={{
				borderBottom: `1px solid ${borderColor}`,
				...stickyStyles,
			}}
		>
			<Flex
				align="center"
				justify="space-between"
				sx={{
					height: "100%",
				}}
			>
				<HamburgerMenu />
				<Group>
					<div className="relative flex">
						<Menu closeOnClickOutside>
							<Menu.Target>
								<div className="cursor-pointer">
									<IconLanguage className="cursor-pointer" />
								</div>
							</Menu.Target>
							<Menu.Dropdown>
								{[...(i18n.languages || [])].sort().map((lang: string) => (
									<Menu.Item
										key={lang}
										color={lang === currentLocale ? "green" : undefined}
										onClick={() => changeLanguage(lang)}
										icon={
											<span style={{ marginRight: 8 }}>
												<Avatar size={16} src={`/images/flags/${lang}.svg`} />
											</span>
										}
									>
										{lang === "en" && "English"}
										{lang === "es" && "Español"}
										{lang === "fr" && "Français"}
										{lang === "ar" && "عربي"}
									</Menu.Item>
								))}
							</Menu.Dropdown>
						</Menu>
					</div>
					<ActionIcon
						variant="outline"
						color={dark ? "yellow" : "primary"}
						onClick={() => toggleColorScheme()}
						title="Toggle color scheme"
					>
						{dark ? <IconSun size={18} /> : <IconMoonStars size={18} />}
					</ActionIcon>
					{(user?.name || user?.avatar) && (
						<Group spacing="xs">
							{user?.name && <Title order={6}>{user?.name}</Title>}
							<Avatar src={user?.avatar} alt={user?.name} radius="xl" />
						</Group>
					)}
				</Group>
			</Flex>
		</MantineHeader>
	);
};

export default Header;
