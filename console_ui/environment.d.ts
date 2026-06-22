declare global {
	namespace NodeJS {
		interface ProcessEnv {
			NEXT_PUBLIC_API_URL: string;
			NEXT_PUBLIC_ENV: string;
			NEXT_PUBLIC_DEV_ADMIN_EMAIL: string;
			NEXT_PUBLIC_AUTH_COOKIE: string;
			NEXT_PUBLIC_USER_INFO_COOKIE_NAME: string;
			NEXT_PUBLIC_ENV_LOGIN_URL?: string;
			NEXT_PUBLIC_ENV_LOGOUT_URL?: string;
			NEXT_PUBLIC_PLATFORM_DOMAIN_BASE?: string;
			NEXT_PUBLIC_PLATFORM_SCHEMA_BASE?: string;
			NEXT_PUBLIC_SENTRY_DSN?: string;
			NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE?: number;
			NEXT_PUBLIC_SENTRY_RELEASE: string;
			NEXT_PUBLIC_SENTRY_DEBUG?: boolean;
			NEXT_PUBLIC_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE?: number;
			NEXT_PUBLIC_SENTRY_REPLAYS_SESSION_SAMPLE_RATE?: number;
			SENTRY_ORG?: string;
			SENTRY_PROJECT?: string;
		}
	}
}

// If this file has no import/export statements (i.e. is a script)
// convert it into a module by adding an empty export statement.
export {};
