"use client";

import { getUserRole } from "@providers/auth-provider";
import { CanParams } from "@refinedev/core";

const accessControlProvider = {
	can: async ({ resource, action }: CanParams): Promise<any> => {
		// Check if the resource is "projects" and the action is "create" or "edit"
		if (resource === "projects" && ["create", "edit"].includes(action)) {
			// Get the user's role
			const userRole = await getUserRole();
			// Only allow access if the user is an admin
			if (userRole === "admin") {
				return { can: true };
			}
			// Return false to deny access
			return { can: false };
		}
		// Allow access for other actions/resources
		return { can: true };
	},
	options: {
		buttons: {
			enableAccessControl: true,
			hideIfUnauthorized: true,
		},
	},
};

export default accessControlProvider;
