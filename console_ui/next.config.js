module.exports = {
	transpilePackages: ["@refinedev/nextjs-router"],
	async rewrites() {
		if (!process.env.PHOENIX_INTERNAL_API_URL) {
			return [];
		}
		return [
			{
				source: "/api/:path*",
				destination: `${process.env.PHOENIX_INTERNAL_API_URL}/:path*`,
			},
		];
	},
	webpack(config) {
		config.module.rules.push({
			test: /\.svg$/,
			use: ["@svgr/webpack"],
		});

		return config;
	},
};

// Injected content via Sentry wizard below

const { withSentryConfig } = require("@sentry/nextjs");

const sentry_dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
const sentry_org = process.env.SENTRY_ORG;
const sentry_project = process.env.SENTRY_PROJECT;

if (sentry_dsn && sentry_org && sentry_project) {
	console.log("Sentry DSN found, enabling error monitoring");
	module.exports = withSentryConfig(module.exports, {
		// For all available options, see:
		// https://github.com/getsentry/sentry-webpack-plugin#options

		org: sentry_org,
		project: sentry_project,

		// Only print logs for uploading source maps in CI
		silent: !process.env.CI,

		// For all available options, see:
		// https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

		// Upload a larger set of source maps for prettier stack traces (increases build time)
		widenClientFileUpload: true,

		// Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
		// This can increase your server load as well as your hosting bill.
		// Note: Check that the configured route will not match with your Next.js middleware, otherwise reporting of client-
		// side errors will fail.
		tunnelRoute: "/monitoring",

		// Hides source maps from generated client bundles
		hideSourceMaps: true,

		// Automatically tree-shake Sentry logger statements to reduce bundle size
		disableLogger: true,

		// Enables automatic instrumentation of Vercel Cron Monitors. (Does not yet work with App Router route handlers.)
		// See the following for more information:
		// https://docs.sentry.io/product/crons/
		// https://vercel.com/docs/cron-jobs
		automaticVercelMonitors: true,
	});
}
