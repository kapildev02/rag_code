import { useState, useEffect } from "react";
import { useAppDispatch } from "@/store/hooks";
import { Button } from "@/components/atoms/Button/Button";
import {
	orgResetChromaApi,
	orgResetMongoApi,
	orgDeleteFileApi,
	orgGetFilesApi,
	orgGetCategoryNameApi,
} from "@/services/adminApi";
import toast from "react-hot-toast";
import { AlertTriangle, Trash2, RotateCw, Database } from "lucide-react";
import { motion } from "framer-motion";

type FileType = {
	id: string;
	filename: string;
	category_id: string;
	category_name?: string;
};

type ConfirmAction = {
	open: boolean;
	actionType: "mongodb" | "indexes" | null;
	input: string;
};

const AdditionalTab = () => {
	const dispatch = useAppDispatch();
	const [loading, setLoading] = useState(false);
	const [fileId, setFileId] = useState("");
	const [files, setFiles] = useState<FileType[]>([]);
	const [confirm, setConfirm] = useState<ConfirmAction>({
		open: false,
		actionType: null,
		input: "",
	});

	const groupedFiles = files.reduce((acc, file) => {
		const categoryName = file.category_name || "Uncategorized";
		if (!acc[categoryName]) {
			acc[categoryName] = [];
		}
		acc[categoryName].push(file);
		return acc;
	}, {} as Record<string, FileType[]>);

	useEffect(() => {
		const fetchFiles = async () => {
			try {
				const response = await dispatch(orgGetFilesApi()).unwrap();
				if (response.success && Array.isArray(response.data)) {
					const filesWithCategories = await fetchCategoryNames(response.data);
					setFiles(filesWithCategories);
				}
			} catch {
				toast.error("Failed to fetch files");
			}
		};
		fetchFiles();
	}, [dispatch]);

	const fetchCategoryNames = async (files: FileType[]) => {
		const uniqueCategoryIds = [...new Set(files.map((file) => file.category_id))];
		try {
			const categoryPromises = uniqueCategoryIds.map((categoryId) =>
				dispatch(orgGetCategoryNameApi(categoryId)).unwrap()
			);
			const categoryResponses = await Promise.all(categoryPromises);
			const categoryMap = categoryResponses.reduce((acc, response) => {
				if (response.success && response.data) {
					acc[response.data.id] = response.data.name;
				}
				return acc;
			}, {} as Record<string, string>);
			return files.map((file) => ({
				...file,
				category_name: categoryMap[file.category_id] || "Uncategorized",
			}));
		} catch (error) {
			toast.error("Failed to fetch category names");
			return files;
		}
	};

	const triggerReset = (type: "mongodb" | "indexes") => {
		setConfirm({ open: true, actionType: type, input: "" });
	};

	const handleConfirm = async () => {
		if (!confirm.actionType) return;
		setLoading(true);
		setConfirm({ open: false, actionType: null, input: "" });
		try {
			let response;
			if (confirm.actionType === "mongodb") {
				response = await dispatch(orgResetMongoApi()).unwrap();
			} else {
				response = await dispatch(orgResetChromaApi()).unwrap();
			}
			toast[response.success ? "success" : "error"](
				response.success
					? `${confirm.actionType} reset successfully`
					: `Failed to reset ${confirm.actionType}`
			);
		} catch (err: any) {
			toast.error(
				`Error resetting ${confirm.actionType}: ` + (err.message || "Unknown error")
			);
		} finally {
			setLoading(false);
		}
	};

	const handleDeleteFile = async () => {
		if (!fileId) {
			toast.error("Please select a file");
			return;
		}
		setLoading(true);
		try {
			const response = await dispatch(orgDeleteFileApi(fileId)).unwrap();
			toast[response.success ? "success" : "error"](
				response.success ? "File deleted successfully" : "Failed to delete file"
			);
			if (response.success) {
				setFiles((prev) => prev.filter((file) => file.id !== fileId));
				setFileId("");
			}
		} catch (err: any) {
			toast.error("Error deleting file: " + (err.message || "Unknown error"));
		} finally {
			setLoading(false);
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 10 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.3 }}
		>
			<div className="mb-8">
				<div className="flex items-center gap-3 mb-2">
					<AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
					<h1 className="text-3xl font-bold text-gray-900 dark:text-white">
						Additional Tools
					</h1>
				</div>
				<p className="text-gray-600 dark:text-gray-400">
					Advanced ingestion management
				</p>
			</div>

			{/* Reset Section */}
			<motion.div
				initial={{ opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ delay: 0.1 }}
				className="card border-red-200 dark:border-red-900/50 mb-8"
			>
				<div className="flex items-center gap-3 mb-6">
					<Database className="w-6 h-6 text-red-600 dark:text-red-400" />
					<h2 className="text-xl font-semibold text-gray-900 dark:text-white">
						Reset Database
					</h2>
				</div>
				<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<motion.button
						whileHover={{ scale: 1.02 }}
						whileTap={{ scale: 0.98 }}
						onClick={() => triggerReset("indexes")}
						disabled={loading}
						className="p-4 rounded-lg border-2 border-red-300 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors group"
					>
						<div className="flex items-center gap-3 justify-center">
							<RotateCw className="w-5 h-5 text-red-600 dark:text-red-400 group-hover:animate-spin" />
							<div className="text-left">
								<p className="font-semibold text-gray-900 dark:text-white">
									Reset Indexes
								</p>
								<p className="text-sm text-gray-600 dark:text-gray-400">
									Clear vector indexes
								</p>
							</div>
						</div>
					</motion.button>

					<motion.button
						whileHover={{ scale: 1.02 }}
						whileTap={{ scale: 0.98 }}
						onClick={() => triggerReset("mongodb")}
						disabled={loading}
						className="p-4 rounded-lg border-2 border-yellow-300 dark:border-yellow-900/50 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors group"
					>
						<div className="flex items-center gap-3 justify-center">
							<RotateCw className="w-5 h-5 text-yellow-600 dark:text-yellow-400 group-hover:animate-spin" />
							<div className="text-left">
								<p className="font-semibold text-gray-900 dark:text-white">
									Reset MongoDB
								</p>
								<p className="text-sm text-gray-600 dark:text-gray-400">
									Clear document database
								</p>
							</div>
						</div>
					</motion.button>
				</div>
			</motion.div>

			{/* File Deletion Section */}
			<motion.div
				initial={{ opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ delay: 0.2 }}
				className="card mb-8"
			>
				<div className="flex items-center gap-3 mb-6">
					<Trash2 className="w-6 h-6 text-red-600 dark:text-red-400" />
					<h2 className="text-xl font-semibold text-gray-900 dark:text-white">
						Delete File
					</h2>
				</div>
				<div className="space-y-4">
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Select File
						</label>
						<select
							value={fileId}
							onChange={(e) => setFileId(e.target.value)}
							className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
						>
							<option value="">Choose a file to delete</option>
							{Object.entries(groupedFiles).map(([category, fileList]) => (
								<optgroup key={category} label={category}>
									{fileList.map((file) => (
										<option key={file.id} value={file.id}>
											{file.filename}
										</option>
									))}
								</optgroup>
							))}
						</select>
					</div>
					<Button
						onClick={handleDeleteFile}
						disabled={loading || !fileId}
						className="w-full bg-red-600 hover:bg-red-700 text-white"
					>
						<Trash2 className="w-4 h-4 mr-2" />
						Delete File
					</Button>
				</div>
			</motion.div>

			{/* Files by Category */}
			<motion.div
				initial={{ opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ delay: 0.3 }}
			>
				<h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
					<Database className="w-6 h-6" />
					Files by Category
				</h2>
				<div className="space-y-4">
					{Object.entries(groupedFiles).length === 0 ? (
						<div className="card text-center py-8">
							<p className="text-gray-600 dark:text-gray-400">No files found</p>
						</div>
					) : (
						Object.entries(groupedFiles).map(([category, fileList]) => (
							<motion.div
								key={category}
								initial={{ opacity: 0 }}
								animate={{ opacity: 1 }}
								className="card border-l-4 border-primary-500"
							>
								<h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
									<Database className="w-4 h-4 text-primary-500" />
									{category}
								</h3>
								<ul className="space-y-2">
									{fileList.map((file) => (
										<li
											key={file.id}
											className="flex items-center gap-2 text-gray-700 dark:text-gray-300 text-sm"
										>
											<span className="w-2 h-2 rounded-full bg-accent-500" />
											{file.filename}
										</li>
									))}
								</ul>
							</motion.div>
						))
					)}
				</div>
			</motion.div>

			{/* Confirmation Modal */}
			{confirm.open && (
				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					exit={{ opacity: 0 }}
					className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
				>
					<motion.div
						initial={{ scale: 0.95, opacity: 0 }}
						animate={{ scale: 1, opacity: 1 }}
						className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-700"
					>
						<div className="flex items-center gap-3 mb-4">
							<AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
							<h2 className="text-lg font-semibold text-gray-900 dark:text-white">
								Confirm Reset
							</h2>
						</div>
						<p className="text-gray-600 dark:text-gray-400 mb-4">
							Type{" "}
							<span className="font-semibold">
								reset {confirm.actionType}
							</span>{" "}
							to confirm this action.
						</p>
						<input
							type="text"
							value={confirm.input}
							onChange={(e) =>
								setConfirm((prev) => ({ ...prev, input: e.target.value }))
							}
							placeholder={`reset ${confirm.actionType}`}
							className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-6 focus:outline-none focus:ring-2 focus:ring-primary-500"
						/>
						<div className="flex gap-3">
							<Button
								onClick={() =>
									setConfirm({ open: false, actionType: null, input: "" })
								}
								className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600"
							>
								Cancel
							</Button>
							<Button
								onClick={handleConfirm}
								disabled={
									confirm.input.trim().toLowerCase() !==
									`reset ${confirm.actionType}`
								}
								className="flex-1 bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Confirm
							</Button>
						</div>
					</motion.div>
				</motion.div>
			)}
		</motion.div>
	);
};

export default AdditionalTab;
