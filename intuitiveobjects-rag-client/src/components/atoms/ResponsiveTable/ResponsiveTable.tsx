import React from "react";
import { motion } from "framer-motion";
import { Loader } from "../Loading/Loading";

interface Column {
	key: string;
	header: string;
	render?: (value: any, row: any) => React.ReactNode;
	className?: string;
}

interface ResponsiveTableProps {
	columns: Column[];
	data: any[];
	emptyMessage?: string;
	className?: string;
	isLoading?: boolean;
}

export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
	columns,
	data,
	emptyMessage = "No data available",
	className = "",
	isLoading = false,
}) => {
	if (isLoading) {
		return (
			<div className="py-8 text-center">
				<Loader />
			</div>
		);
	}

	if (!data || data.length === 0) {
		return (
			<div className="text-center py-12 text-gray-500 dark:text-gray-400">
				<p className="text-base">{emptyMessage}</p>
			</div>
		);
	}

	const containerVariants = {
		hidden: { opacity: 0 },
		visible: {
			opacity: 1,
			transition: { staggerChildren: 0.05 },
		},
	};

	const itemVariants = {
		hidden: { opacity: 0, y: 10 },
		visible: { opacity: 1, y: 0 },
	};

	return (
		<div className={`overflow-hidden rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
			{/* Desktop Table View */}
			<div className="hidden md:block overflow-x-auto">
				<table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead className="bg-gray-50 dark:bg-gray-800">
						<tr>
							{columns.map((column) => (
								<th
									key={column.key}
									scope="col"
									className={`px-6 py-4 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider ${
										column.className || ""
									}`}
								>
									{column.header}
								</th>
							))}
						</tr>
					</thead>
					<motion.tbody
						variants={containerVariants}
						initial="hidden"
						animate="visible"
						className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800"
					>
						{data.map((row, rowIndex) => (
							<motion.tr
								key={rowIndex}
								variants={itemVariants}
								className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
							>
								{columns.map((column) => (
									<td
										key={`${rowIndex}-${column.key}`}
										className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 ${
											column.className || ""
										}`}
									>
										{column.render
											? column.render(row[column.key], row)
											: row[column.key]}
									</td>
								))}
							</motion.tr>
						))}
					</motion.tbody>
				</table>
			</div>

			{/* Mobile Card View */}
			<motion.div
				variants={containerVariants}
				initial="hidden"
				animate="visible"
				className="md:hidden space-y-3 p-4"
			>
				{data.map((row, rowIndex) => (
					<motion.div
						key={rowIndex}
						variants={itemVariants}
						className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
					>
						{columns.map((column) => (
							<div
								key={`${rowIndex}-${column.key}`}
								className="flex justify-between items-start py-2 border-b border-gray-200 dark:border-gray-700 last:border-0"
							>
								<span className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
									{column.header}
								</span>
								<div className="text-sm text-right text-gray-900 dark:text-gray-100">
									{column.render
										? column.render(row[column.key], row)
										: row[column.key]}
								</div>
							</div>
						))}
					</motion.div>
				))}
			</motion.div>
		</div>
	);
};
