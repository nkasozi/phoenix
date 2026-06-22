// This file configures the initialization of Sentry on the client.
// The config you add here will be used whenever a users loads a page in their browser.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const SENTRY_TRACES_SAMPLE_RATE =
	process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || 1;
const SENTRY_DEBUG = process.env.NEXT_PUBLIC_SENTRY_DEBUG || false;
const SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE =
	process.env.NEXT_PUBLIC_SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE || 1.0;
const SENTRY_REPLAYS_SESSION_SAMPLE_RATE =
	process.env.NEXT_PUBLIC_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || 0.1;
const SENTRY_RELEASE = process.env.NEXT_PUBLIC_SENTRY_RELEASE!;
const ENV = process.env.NEXT_PUBLIC_ENV;

if (!SENTRY_DSN) {
	console.warn("NEXT_PUBLIC_SENTRY_DSN is not set");
} else {
	Sentry.init({
		dsn: SENTRY_DSN,

		release: SENTRY_RELEASE,

		environment: ENV,

		// Adjust this value in production, or use tracesSampler for greater control
		tracesSampleRate: SENTRY_TRACES_SAMPLE_RATE,

		// Setting this option to true will print useful information to the console while you're setting up Sentry.
		debug: SENTRY_DEBUG,

		replaysOnErrorSampleRate: SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE,

		// This sets the sample rate to be 10%. You may want this to be 100% while
		// in development and sample at a lower rate in production
		replaysSessionSampleRate: SENTRY_REPLAYS_SESSION_SAMPLE_RATE,

		// You can remove this option if you're not planning to use the Sentry Session Replay feature:
		integrations: [
			Sentry.replayIntegration({
				// Additional Replay configuration goes in here, for example:
				maskAllText: true,
				blockAllMedia: true,
			}),
		],
	});
}
