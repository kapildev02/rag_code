import { Button } from "@/components/atoms/Button/Button";
import { Icon } from "@/components/atoms/Icon/Icon";
import { Loader } from "@/components/atoms/Loading/Loading";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useParams } from "react-router-dom";
import { Chat } from "@/services/chatApi";
import MoreHorizIcon from "@/components/atoms/Icon/MoreHorizIcon";
import { Menu, MenuButton, MenuItems, MenuItem } from "@headlessui/react";
import { TrashIcon } from "@/components/atoms/Icon/Trash";
import EditIcon from "@/components/atoms/Icon/EditIcon";
import { useState } from "react";
import { TextInput } from "@/components/atoms/TextInput";
import { deleteChatApi, editChatApi } from "@/services/chatApis";
import { toast } from "react-hot-toast";
import { confirmAction } from "@/utils/sweetAlert";
import { Plus, MessageSquare, Trash2, Edit3 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Conversation {
	id: string;
	title: string;
	timestamp: string;
}

interface SidebarProps {
	isOpen: boolean;
	conversations: Conversation[];
	onNewChat: () => void;
	onSelectChat: (id: string) => void;
	selectedId?: string;
	onClose?: () => void;
	isLoading: boolean;
}

export const Sidebar = ({
	isOpen,
	onNewChat,
	onSelectChat,
	onClose,
	isLoading,
}: SidebarProps) => {
	const history = useAppSelector((state) => state.chat.history);
	const { chatId } = useParams();

	return (
		<>
			{/* Overlay */}
			{isOpen && (
				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					exit={{ opacity: 0 }}
					className="fixed inset-0 bg-black/50 transition-opacity lg:hidden z-20"
					onClick={onClose}
					aria-hidden="true"
				/>
			)}

			<motion.aside
				initial={isOpen ? { x: 0 } : { x: "-100%" }}
				animate={isOpen ? { x: 0 } : { x: "-100%" }}
				transition={{ type: "spring", stiffness: 300, damping: 30 }}
				/* place sidebar below the sticky header (header height = 4rem)
				   and make it span the remaining viewport height so its top
				   controls (New Chat button) are not covered by the header */
				className="fixed top-16 left-0 h-[calc(100vh-4rem)] w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 lg:translate-x-0 z-30 flex flex-col"
			>
				{/* New Chat Button */}
				<div className="p-4 border-b border-gray-200 dark:border-gray-700">
					<motion.button
						onClick={onNewChat}
						className="w-full btn-primary flex items-center justify-center gap-2"
						whileHover={{ scale: 1.02 }}
						whileTap={{ scale: 0.98 }}
					>
						<Plus className="w-4 h-4" />
						New Chat
					</motion.button>
				</div>

				{/* Chat History */}
				<div className="flex-1 overflow-y-auto p-4">
					{isLoading ? (
						<div className="flex justify-center items-center h-full">
							<Loader />
						</div>
					) : history && history.length > 0 ? (
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							className="space-y-2"
						>
							<AnimatePresence mode="popLayout">
								{history.map((conv) => (
									<ChatItem
										key={conv.id}
										conv={conv}
										isActive={chatId === conv.id}
										onSelectChat={onSelectChat}
									/>
								))}
							</AnimatePresence>
						</motion.div>
					) : (
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							className="flex flex-col items-center justify-center h-full text-center py-8"
						>
							<MessageSquare className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
							<p className="text-sm text-gray-500 dark:text-gray-400">
								No conversations yet
							</p>
							<p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
								Start a new chat to begin
							</p>
						</motion.div>
					)}
				</div>
			</motion.aside>
		</>
	);
};

interface ChatItemProps {
	conv: Chat;
	isActive: boolean;
	onSelectChat: (id: string) => void;
}

const ChatItem = ({ conv, isActive, onSelectChat }: ChatItemProps) => {
	const dispatch = useAppDispatch();
	const [isEditing, setIsEditing] = useState(false);
	const [editedName, setEditedName] = useState(conv.name);

	const onRenameChatBtnClick = () => {
		setIsEditing(true);
		setEditedName(conv.name);
	};

	const onDeleteBtnClick = () => {
		confirmAction(
			"Are you sure?",
			"You won't be able to revert this!",
			"Yes, delete it!"
		).then(async (result) => {
			if (result.isConfirmed) {
				const res = await dispatch(deleteChatApi(conv.id));
				if (deleteChatApi.fulfilled.match(res)) {
					toast.success("Chat deleted");
				} else {
					toast.error("Failed to delete chat");
				}
			}
		});
	};

	const handleRenameChat = async () => {
		setIsEditing(false);
		if (editedName === conv.name || editedName.length === 0) {
			return;
		}
		const res = await dispatch(
			editChatApi({ chatId: conv.id, name: editedName })
		);
		if (editChatApi.fulfilled.match(res)) {
			toast.success("Chat renamed");
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, x: -10 }}
			animate={{ opacity: 1, x: 0 }}
			exit={{ opacity: 0, x: -10 }}
			whileHover={{ x: 4 }}
			className="w-full"
		>
			<Button
				onClick={() => onSelectChat(conv.id)}
				className={`w-full text-left p-3 rounded-lg transition-all duration-200 flex items-center gap-2 group ${
					isActive
						? "bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg"
						: "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
				}`}
			>
				<MessageSquare
					className={`w-4 h-4 flex-shrink-0 ${
						isActive ? "text-white" : "text-gray-500 dark:text-gray-400"
					}`}
				/>
				<div className="flex-1 min-w-0 flex items-center justify-between gap-2">
					<div className="truncate flex-1">
						{isEditing ? (
							<TextInput
								value={editedName}
								onChange={(e) => setEditedName(e.target.value)}
								hideLabel
								className="!px-2 !py-1 !text-sm rounded"
								onBlur={handleRenameChat}
								onKeyDown={(e) => {
									if (e.key === "Enter") {
										handleRenameChat();
									}
								}}
								autoFocus
							/>
						) : (
							<span className="text-sm font-medium block truncate">
								{conv.name}
							</span>
						)}
					</div>

					{!isEditing && (
						<Menu
							as="div"
							className="relative inline-block text-left opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
						>
							<MenuButton className="p-1.5 hover:bg-white/20 dark:hover:bg-black/20 rounded flex items-center justify-center">
								<MoreHorizIcon
									className={`fill-current ${
										isActive ? "text-white" : ""
									}`}
								/>
							</MenuButton>
							<MenuItems className="absolute right-0 mt-1 w-40 origin-top-right bg-white dark:bg-gray-800 rounded-lg shadow-xl ring-1 ring-black/5 focus:outline-none z-50">
								<MenuItem>
									{({ active }) => (
										<button
											onClick={onRenameChatBtnClick}
											className={`w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 transition-colors ${
												active ? "bg-gray-100 dark:bg-gray-700" : ""
											}`}
										>
											<Edit3 className="w-4 h-4" />
											Rename
										</button>
									)}
								</MenuItem>
								<MenuItem>
									{({ active }) => (
										<button
											onClick={onDeleteBtnClick}
											className={`w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 text-red-600 dark:text-red-400 transition-colors ${
												active ? "bg-red-50 dark:bg-red-900/20" : ""
											}`}
										>
											<Trash2 className="w-4 h-4" />
											Delete
										</button>
									)}
								</MenuItem>
							</MenuItems>
						</Menu>
					)}
				</div>
			</Button>
		</motion.div>
	);
};
