import axios from "@providers/data-provider/axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface UpdateUserPayload {
	display_name: string;
	app_role: string;
}

export default class UserService {
	async updateUser(id: number, data: UpdateUserPayload) {
		const response = await axios.put(`${API_URL}/users/${id}`, data);
		return response;
	}
}
