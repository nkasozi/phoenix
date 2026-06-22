const path = require("path");

module.exports = {
	i18n: {
		defaultLocale: "en",
		locales: ["en", "de", "fr", "ar"],
	},
	localePath: path.resolve("./public/locales"),
};
