export interface ClassData {
	id?: number;
	tempId?: number;
	name: string;
	description: string;
}

export interface Author {
	phoenix_platform_message_author_id: string;
	pi_platform_message_author_id: string;
	pi_platform_message_author_name: string;
	phoenix_processed_at: string;
	platform: string;
	post_count: number;
	pi_author_link?: string;
	intermediatory_author_classes: {
		class_id: number;
		class_name: string;
		id: number;
	}[];
}
