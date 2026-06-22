import { useState, useCallback, useRef } from "react";

export type SaveStatus = "saving" | "saved" | "error";

export function useSaveStatus() {
	const [statusMap, setStatusMap] = useState<Map<string, SaveStatus>>(
		new Map()
	);
	const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(
		new Map()
	);

	const setSaving = useCallback((id: string) => {
		// Clear any existing auto-clear timer
		const existing = timersRef.current.get(id);
		if (existing) clearTimeout(existing);
		setStatusMap((prev) => new Map(prev).set(id, "saving"));
	}, []);

	const setSaved = useCallback((id: string) => {
		setStatusMap((prev) => new Map(prev).set(id, "saved"));
		// Auto-clear after 2 seconds
		const timer = setTimeout(() => {
			setStatusMap((prev) => {
				const next = new Map(prev);
				if (next.get(id) === "saved") {
					next.delete(id);
				}
				return next;
			});
			timersRef.current.delete(id);
		}, 2000);
		timersRef.current.set(id, timer);
	}, []);

	const setError = useCallback((id: string) => {
		const existing = timersRef.current.get(id);
		if (existing) clearTimeout(existing);
		setStatusMap((prev) => new Map(prev).set(id, "error"));
	}, []);

	const getStatus = useCallback(
		(id: string): SaveStatus | undefined => {
			return statusMap.get(id);
		},
		[statusMap]
	);

	const clearStatus = useCallback((id: string) => {
		const existing = timersRef.current.get(id);
		if (existing) clearTimeout(existing);
		timersRef.current.delete(id);
		setStatusMap((prev) => {
			const next = new Map(prev);
			next.delete(id);
			return next;
		});
	}, []);

	const hasPendingSaves = useCallback((): boolean => {
		let pending = false;
		statusMap.forEach((status) => {
			if (status === "saving") pending = true;
		});
		return pending;
	}, [statusMap]);

	return {
		setSaving,
		setSaved,
		setError,
		getStatus,
		clearStatus,
		hasPendingSaves,
		statusMap,
	};
}
