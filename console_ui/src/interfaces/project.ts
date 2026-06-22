export type ProjectSchema = {
	name: string;
	description: string;
	workspace_slug: string;
	days_until_pi_expiration: number;
	days_until_all_data_expiration: number;
	expected_usage: string;
	has_unlimited_credits: boolean;
	dashboard_id: number;
};
