import { ReactNode } from "react";
import { AdminHeader } from "@/components/organisms/Admin/AdminHeader/AdminHeader";
import { Outlet } from "react-router-dom";
import { motion } from "framer-motion";

interface AdminLayoutProps {
	children?: ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
	return (
		<div className="min-h-screen bg-gradient-to-br from-background via-white to-blue-50 dark:from-dark-bg dark:via-gray-900 dark:to-gray-800">
			<AdminHeader />
			<motion.div
				initial={{ opacity: 0 }}
				animate={{ opacity: 1 }}
				transition={{ duration: 0.3 }}
				className="flex"
			>
				<div className="flex-1 p-6 sm:p-8 md:p-12">{children || <Outlet />}</div>
			</motion.div>
		</div>
	);
};
