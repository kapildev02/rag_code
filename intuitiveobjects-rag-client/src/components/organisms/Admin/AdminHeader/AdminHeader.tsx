import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { adminLogout } from "@/store/slices/authSlice";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { useNavigate } from "react-router-dom";
import { confirmAction } from "@/utils/sweetAlert";
import { LogOut } from "lucide-react";
import { MessageSquare } from "lucide-react";
import { motion } from "framer-motion";

export const AdminHeader = () => {
	const dispatch = useAppDispatch();
	const navigate = useNavigate();
	const admin = useAppSelector((state) => state.auth.admin?.user);

	// navigate to admin chat
	const openAdminChat = () => {
		navigate("/admin/chat");
	};

	// Get initials for avatar
	const getInitials = () => {
		if (!admin?.name && !admin?.email) return "A";
		if (admin?.name) return admin.name.charAt(0).toUpperCase();
		return admin.email.charAt(0).toUpperCase();
	};

	const handleLogout = () => {
		confirmAction("Logout", "Are you sure you want to logout?", "Yes, logout").then((result) => {
			if (result.isConfirmed) {
				dispatch(adminLogout());
				navigate("/login");
			}
		});
	};

	return (
		<header className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 backdrop-blur-xl bg-opacity-80 dark:bg-opacity-80">
			<div className="mx-auto px-6 h-16 flex items-center justify-between">
				{/* Logo/Title */}
				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					className="flex items-center gap-3"
				>
					<div className="p-2 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-lg">
						<div className="w-6 h-6 rounded-full bg-gradient-to-r from-primary-500 to-accent-500" />
					</div>
					<h1 className="text-xl font-bold gradient-text">Admin Dashboard</h1>
					{/* Chat button */}
					<button
						onClick={openAdminChat}
						title="Open Admin Chat"
						className="ml-2 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none"
					>
						<MessageSquare className="w-5 h-5 text-gray-700 dark:text-gray-200" />
					</button>
				</motion.div>

				{/* User Menu */}
				<Menu as="div" className="relative">
					<MenuButton className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none">
						<div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-semibold text-sm">
							{admin?.avatar ? (
								<img src={admin.avatar} alt="User avatar" className="w-full h-full object-cover rounded-full" />
							) : (
								getInitials()
							)}
						</div>
						<div className="hidden sm:block text-left">
							<p className="text-sm font-medium text-gray-900 dark:text-white">{admin?.name || "Admin"}</p>
							<p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">{admin?.email}</p>
						</div>
					</MenuButton>

					<MenuItems className="absolute right-0 mt-2 w-56 origin-top-right bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
						<div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 sm:hidden">
							<p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Signed in as</p>
							<p className="text-sm font-medium text-gray-900 dark:text-white">{admin?.name || admin?.email}</p>
						</div>

						<MenuItem>
							{({ active }) => (
								<button
									className={`w-full text-left px-4 py-3 flex items-center gap-3 transition-colors ${
										active ? "bg-gray-100 dark:bg-gray-700" : ""
									}`}
									onClick={handleLogout}
								>
									<LogOut className="w-4 h-4" />
									<span className="text-sm font-medium">Logout</span>
								</button>
							)}
						</MenuItem>
					</MenuItems>
				</Menu>
			</div>
		</header>
	);
};
