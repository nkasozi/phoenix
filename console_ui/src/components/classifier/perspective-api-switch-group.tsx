"use client";

import { Switch } from "@mantine/core";
import React from "react";

interface Props {
	formValues: any;
	onSwitchChange: any;
}

export const perspectiveApiSwitches = [
	{ label: "Toxicity", name: "toxicity" },
	{ label: "Severe Toxicity", name: "severe_toxicity" },
	{ label: "Identity Attack", name: "identity_attack" },
	{ label: "Insult", name: "insult" },
	{ label: "Threat", name: "threat" },
	{ label: "Sexually Explicit", name: "sexually_explicit" },
	{ label: "Flirtation", name: "flirtation" },
];

const PerspectiveApiSwitchGroup: React.FC<Props> = ({
	formValues,
	onSwitchChange,
}) => (
	<div className="space-y-4 w-64">
		{perspectiveApiSwitches.map((item: any) => (
			<Switch
				key={item.name}
				labelPosition="left"
				size="lg"
				radius="md"
				className="justify-between"
				label={item.label}
				checked={formValues[item.name]}
				onChange={() => onSwitchChange(item.name)}
			/>
		))}
	</div>
);

export default PerspectiveApiSwitchGroup;
