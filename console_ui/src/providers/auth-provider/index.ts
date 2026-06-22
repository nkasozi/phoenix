"use client";

import { showNotification } from "@mantine/notifications";
import { AuthProvider } from "@refinedev/core";
import { UserInfo } from "src/interfaces/user";
import { storageService } from "src/services";

const DEV_AUTH_COOKIE = "phiphi-user-email";
const USER_INFO_COOKIE_NAME = process.env.NEXT_PUBLIC_USER_INFO_COOKIE_NAME!;
const API_URL = process.env.NEXT_PUBLIC_API_URL!;
const AUTH_URL = process.env.NEXT_PUBLIC_ENV_AUTH_URL!;
const AUTH_COOKIE = process.env.NEXT_PUBLIC_ENV_AUTH_COOKIE!;
const LOGIN_URL = process.env.NEXT_PUBLIC_ENV_LOGIN_URL!;
const LOGOUT_URL = process.env.NEXT_PUBLIC_ENV_LOGOUT_URL!;
const ENV = process.env.NEXT_PUBLIC_ENV!;
const DEV_LOGIN_EMAIL = process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL!;

let HAVE_RESET_USER_INFO_COOKIE = false;

const getLoginUrl = () => {
	const current_url = window.location.href;
	return `${LOGIN_URL}?rd=${current_url}`;
};

const redirectToLoginPage = () => {
	if (ENV !== "dev" && LOGIN_URL) {
		window.location.href = getLoginUrl();
	}
};

const redirectToLogoutPage = () => {
	if (ENV !== "dev" && LOGOUT_URL) {
		window.location.href = LOGOUT_URL;
	}
};

const fetchUserInfo = async (): Promise<UserInfo | null> => {
	try {
		const response = await fetch(`${API_URL}/users/me`, {
			method: "GET",
			credentials: "include",
		});
		if (!response.ok) {
			throw new Error(`HTTP error! Status: ${response.status}`);
		}
		const userData: UserInfo = await response.json();
		return userData;
	} catch (error) {
		// Handle any other errors, including network errors
		showNotification({
			title: "Error",
			message: "An error occurred while fetching user data.",
			color: "red",
		});
		return null;
	}
};

const checkAuthUrl = async (url: string): Promise<boolean> => {
	try {
		const response = await fetch(url, {
			method: "GET",
			credentials: "include",
		});
		if (response.ok) {
			return true;
		}
		return false;
	} catch (error) {
		return false;
	}
};

export const getCurrentUserInfo = () => {
	const userInfoFromCookie = storageService.get(USER_INFO_COOKIE_NAME);
	return userInfoFromCookie ? JSON.parse(userInfoFromCookie) : null;
};

export const setUserInfoFromAPI = async (): Promise<UserInfo | null> => {
	const userInfo = await fetchUserInfo();
	storageService.set(USER_INFO_COOKIE_NAME, JSON.stringify(userInfo));
	return userInfo;
};

export const getUserRole = async (): Promise<string | null> => {
	let userInfo = await getCurrentUserInfo();
	if (!userInfo) {
		userInfo = await setUserInfoFromAPI();
	}
	if (userInfo && Object.hasOwn(userInfo, "app_role")) {
		return userInfo.app_role;
	}
	return null;
};

const checkAuth = async (): Promise<boolean> => {
	// For this to work the cookie must not be http only
	// In oauth2-proxy use cookie_httponly=false
	if (AUTH_COOKIE && storageService.get(AUTH_COOKIE)) {
		return true;
	}
	if (AUTH_URL && (await checkAuthUrl(AUTH_URL))) {
		return true;
	}
	return false;
};

const authProvider: AuthProvider = {
	login: async () => {
		// Remove user info cookie so it can be refreshed after login
		storageService.remove(USER_INFO_COOKIE_NAME);
		if (ENV === "dev") {
			storageService.set(DEV_AUTH_COOKIE, DEV_LOGIN_EMAIL);
		} else {
			redirectToLoginPage();
		}
		return {
			success: false,
			error: new Error("Login failed"),
		};
	},
	logout: async () => {
		storageService.remove(USER_INFO_COOKIE_NAME);
		redirectToLogoutPage();
		return { success: true };
	},
	check: async () => {
		// Reset the user info cookie on the first load of the page
		if (!HAVE_RESET_USER_INFO_COOKIE) {
			HAVE_RESET_USER_INFO_COOKIE = true;
			storageService.remove(USER_INFO_COOKIE_NAME);
		}
		if (ENV === "dev" && storageService.get(DEV_AUTH_COOKIE)) {
			return { authenticated: true };
		}
		if (ENV === "dev") {
			storageService.set(DEV_AUTH_COOKIE, DEV_LOGIN_EMAIL);
			return { authenticated: true };
		}
		if (await checkAuth()) {
			return { authenticated: true };
		}
		return { authenticated: false, redirectTo: getLoginUrl() };
	},
	getIdentity: async () => {
		let userInfo = getCurrentUserInfo();
		if (!userInfo) {
			userInfo = await setUserInfoFromAPI();
		}
		return userInfo;
	},
	onError: async (error) => {
		if (error.response?.status === 401 || error.response?.status === 403) {
			const isAuthenticated = await checkAuthUrl(AUTH_URL);
			if (!isAuthenticated) {
				storageService.remove(USER_INFO_COOKIE_NAME);
				redirectToLoginPage();
			} else {
				showNotification({
					title: "Error",
					// This needs to be translated
					message: "You don't have access to this Request",
					color: "red",
					autoClose: 20000,
				});
				// For some reason this error is not being shown
				return { error: new Error("You don't have access to this Request") };
			}
		} else {
			return { error };
		}
		return { error };
	},
};

export default authProvider;
