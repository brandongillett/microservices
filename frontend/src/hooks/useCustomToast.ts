"use client";

import { toaster } from "@/components/ui";

const useCustomToast = () => {
	const showSuccessToast = (description: string) => {
		toaster.create({
			title: "Success",
			description,
			type: "success",
			duration: 5000,
			meta: {
				closable: true,
			},
		});
	};

	const showErrorToast = (description: string) => {
		toaster.create({
			title: "Error",
			description,
			type: "error",
			duration: 7000,
			meta: {
				closable: true,
			},
		});
	};

	const showInfoToast = (description: string) => {
		toaster.create({
			title: "Info",
			description,
			type: "info",
			duration: 5000,
			meta: {
				closable: true,
			},
		});
	};

	return { showSuccessToast, showErrorToast, showInfoToast };
};

export default useCustomToast;
