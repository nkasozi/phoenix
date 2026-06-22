import { defineConfig, globalIgnores } from "eslint/config";
import nextPlugin from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";
import stylistic from "@stylistic/eslint-plugin";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import jsxA11yPlugin from "eslint-plugin-jsx-a11y";
import importPlugin from "eslint-plugin-import";
import prettierConfig from "eslint-config-prettier";

const config = defineConfig([
	// Global ignores
	globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),

	// Next.js core web vitals config
	nextPlugin.configs["core-web-vitals"],

	// TypeScript ESLint recommended configs
	...tseslint.configs.recommended,

	// React plugin
	{
		files: ["**/*.{js,jsx,ts,tsx}"],
		plugins: {
			react: reactPlugin,
			"react-hooks": reactHooksPlugin,
			"jsx-a11y": jsxA11yPlugin,
			"@stylistic": stylistic,
			import: importPlugin,
		},
		languageOptions: {
			parser: tseslint.parser,
			parserOptions: {
				ecmaVersion: "latest",
				sourceType: "module",
				ecmaFeatures: {
					jsx: true,
				},
				project: "./tsconfig.eslint.json",
				tsconfigRootDir: import.meta.dirname,
			},
		},
		settings: {
			react: {
				version: "detect",
			},
			"import/resolver": {
				node: {
					extensions: [".js", ".jsx", ".ts", ".tsx"],
					paths: ["./src"],
				},
			},
		},
		rules: {
			// TypeScript rules
			"@typescript-eslint/ban-types": "off",
			"@typescript-eslint/explicit-function-return-type": "off",
			"@typescript-eslint/interface-name-prefix": "off",
			"@typescript-eslint/no-empty-object-type": "off",
			"@typescript-eslint/naming-convention": [
				"error",
				{
					selector: "memberLike",
					modifiers: ["private"],
					format: ["camelCase"],
					leadingUnderscore: "require",
				},
			],
			"@typescript-eslint/no-explicit-any": "off",
			"@typescript-eslint/no-unused-vars": [
				"warn",
				{
					argsIgnorePattern: "^_",
					varsIgnorePattern: "^_",
				},
			],

			// React rules
			"react/no-array-index-key": "off",
			"react/prop-types": "off",
			"react/react-in-jsx-scope": "off",
			"react/require-default-props": "off",
			"react/jsx-props-no-spreading": "off",
			"react/function-component-definition": [
				"error",
				{
					namedComponents: [
						"function-declaration",
						"function-expression",
						"arrow-function",
					],
					unnamedComponents: ["function-expression", "arrow-function"],
				},
			],
			"react/no-unstable-nested-components": [
				"warn",
				{
					allowAsProps: true,
				},
			],

			// React Hooks rules
			"react-hooks/exhaustive-deps": "error",

			// Stylistic rules (aligned with Prettier configuration)
			"@stylistic/arrow-parens": ["error", "always"],
			"@stylistic/comma-dangle": [
				"error",
				{
					arrays: "always-multiline",
					objects: "always-multiline",
					imports: "always-multiline",
					exports: "always-multiline",
					functions: "never", // Matches Prettier's "es5" setting
				},
			],
			"@stylistic/indent": [
				"error",
				"tab",
				{
					SwitchCase: 1,
					ignoredNodes: [
						"TemplateLiteral *",
						"JSXElement",
						"JSXElement > *",
						"JSXAttribute",
						"JSXIdentifier",
						"JSXNamespacedName",
						"JSXMemberExpression",
						"JSXSpreadAttribute",
						"JSXExpressionContainer",
						"JSXOpeningElement",
						"JSXClosingElement",
						"JSXFragment",
						"JSXOpeningFragment",
						"JSXClosingFragment",
						"JSXText",
						"JSXEmptyExpression",
						"JSXSpreadChild",
					],
				},
			],
			"@stylistic/quotes": ["error", "double"],
			"@stylistic/semi": ["error", "always"],

			// General rules
			"no-nested-ternary": "off",
			"no-unused-vars": "off", // Handled by @typescript-eslint/no-unused-vars
		},
	},

	// JavaScript-specific overrides (disable TypeScript rules)
	{
		files: ["**/*.js", "**/*.mjs", "**/*.cjs"],
		...tseslint.configs.disableTypeChecked,
		rules: {
			"@typescript-eslint/no-var-requires": "off",
			"@typescript-eslint/no-require-imports": "off",
		},
	},

	// Prettier config - must be last to override conflicting rules
	prettierConfig,
]);

export default config;
