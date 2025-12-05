import { useEffect, useState } from "react";
import { TrashIcon } from "@/components/atoms/Icon/Trash";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import {
	orgDeleteFileApi,
	orgGetCategoriesApi,
	orgGetFilesApi,
} from "@/services/adminApi";
import PdfIcon from "@/components/atoms/Icon/PdfIcon";
import { confirmAction } from "@/utils/sweetAlert";
import { ResponsiveTable } from "@/components/atoms/ResponsiveTable/ResponsiveTable";
import toast from "react-hot-toast";
import GoogleFileUpload from "./GoogleFileUpload";
import LocalFileUpload from "./LocalFileUpload";
import { useSocketContext } from "@/context/SocketContext";
import { updateFiles } from "@/store/slices/adminSlice";
import { Upload, FileText, Calendar, Tag } from "lucide-react";
import { motion } from "framer-motion";

export const IngestionTab = () => {
	const { onDocumentNotifyListener, offDocumentNotifyListener } = useSocketContext();
	const dispatch = useAppDispatch();
	const [isUploading, setIsUploading] = useState(false);

	const categories = useAppSelector((state) => state.admin.categories);
	const files = useAppSelector((state) => state.admin.files);

	const formatFileSize = (sizeInBytes: number) => {
		if (sizeInBytes < 1024) return `${sizeInBytes} B`;
		if (sizeInBytes < 1024 * 1024)
			return `${(sizeInBytes / 1024).toFixed(1)} KB`;
		return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
	};

	const formatDate = (dateString: string) => {
		const date = new Date(dateString);
		return date.toLocaleDateString("en-US", {
			year: "numeric",
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	};

	const getCategoryName = (categoryId: string) => {
		const category = categories.find((cat) => cat.id === categoryId);
		return category ? category.name : "Unknown";
	};

	const handleDeleteFile = async (fileId: string) => {
		confirmAction(
			"Are you sure?",
			"This file will be permanently deleted.",
			"Yes, delete it!"
		).then(async (result: any) => {
			if (result.isConfirmed) {
				const response = await dispatch(orgDeleteFileApi(fileId));
				if (response.payload) {
					toast.success("File deleted successfully");
				} else {
					toast.error("Failed to delete file");
				}
			}
		});
	};

	const notifyListener = async (file: any) => {
		if (file) {
			dispatch(updateFiles(file));
		}
	};

	useEffect(() => {
		dispatch(orgGetCategoriesApi());
		dispatch(orgGetFilesApi());
	}, []);

	useEffect(() => {
		onDocumentNotifyListener(notifyListener);
		return () => {
			offDocumentNotifyListener(notifyListener);
		};
	}, [onDocumentNotifyListener, offDocumentNotifyListener]);

	const columns = [
		{
			key: "filename",
			header: "File Name",
			render: (value: string) => (
				<div className="flex items-center gap-3">
					<div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
						<FileText className="w-4 h-4 text-primary-600 dark:text-primary-400" />
					</div>
					<span className="font-medium text-gray-900 dark:text-white truncate">{value}</span>
				</div>
			),
		},
		{
			key: "category_id",
			header: "Category",
			render: (value: string) => (
				<span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 text-sm font-medium">
					<Tag className="w-3 h-3" />
					{getCategoryName(value)}
				</span>
			),
		},
		{
			key: "file_size",
			header: "Size",
			render: (value: number) => (
				<span className="text-gray-700 dark:text-gray-300">{formatFileSize(value)}</span>
			),
		},
		{
			key: "current_stage",
			header: "Status",
			render: (value: string) => (
				<span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium capitalize">
					{value}
				</span>
			),
		},
		{
			key: "created_at",
			header: "Date",
			render: (value: string) => (
				<div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
					<Calendar className="w-4 h-4" />
					{formatDate(value)}
				</div>
			),
		},
		{
			key: "id",
			header: "Actions",
			className: "text-right",
			render: (id: string) => (
				<motion.button
					whileHover={{ scale: 1.1 }}
					whileTap={{ scale: 0.95 }}
					onClick={() => handleDeleteFile(id)}
					className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
				>
					<TrashIcon />
				</motion.button>
			),
		},
	];

	return (
		<motion.div
			initial={{ opacity: 0, y: 10 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.3 }}
		>
			<div className="mb-8">
				<div className="flex items-center gap-3 mb-2">
					<Upload className="w-8 h-8 text-primary-600 dark:text-primary-400" />
					<h1 className="text-3xl font-bold gradient-text">Document Ingestion</h1>
				</div>
				<p className="text-gray-600 dark:text-gray-400">Upload and manage your documents</p>
			</div>

			{/* Upload Section */}
			<div className="flex flex-col md:flex-row gap-6 mb-8">
				<motion.div
					initial={{ opacity: 0, y: 10 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ delay: 0.1 }}
					className="flex-1 p-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm"
				>
					<LocalFileUpload
						setIsUploading={setIsUploading}
						isUploading={isUploading}
					/>
				</motion.div>

				<motion.div
					initial={{ opacity: 0, y: 10 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ delay: 0.2 }}
					className="flex-1 p-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm"
				>
					<GoogleFileUpload
						setIsUploading={setIsUploading}
						isUploading={isUploading}
					/>
				</motion.div>
			</div>


			{/* Documents Table */}
			<motion.div
				initial={{ opacity: 0, y: 10 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ delay: 0.3 }}
			>
				<div className="mb-4">
					<h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
						<FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />
						Uploaded Documents ({files.length})
					</h2>
				</div>
				<ResponsiveTable
					columns={columns}
					data={files}
					emptyMessage="No documents uploaded yet"
					isLoading={isUploading}
				/>
			</motion.div>
		</motion.div>
	);
};
