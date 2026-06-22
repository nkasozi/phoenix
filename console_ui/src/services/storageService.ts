import cookies from "js-cookie";

const isBrowser = typeof window !== "undefined";

class StorageService {
	get(key: string) {
		return isBrowser ? cookies.get(key) : null;
	}

	set(key: string, value: any, expiresAt?: any) {
		if (isBrowser) {
			cookies.set(key, value, { expires: expiresAt, sameSite: "lax" });
		}
	}

	remove(key: string) {
		if (isBrowser) {
			cookies.remove(key);
		}
	}
}

export default StorageService;
