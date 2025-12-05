import { Button } from "@/components/atoms/Button/Button";
import { Icon } from "@/components/atoms/Icon/Icon";
import { useAppDispatch } from "@/store/hooks";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { userLogout } from "@/store/slices/authSlice";
import { useNavigate } from "react-router-dom";
import PersonIcon from "@/components/atoms/Icon/PersonIcon";
import { Menu as MenuIcon, LogOut } from "lucide-react";
import { motion } from "framer-motion";

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header = ({ onToggleSidebar }: HeaderProps) => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(userLogout());
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 backdrop-blur-xl bg-opacity-80 dark:bg-opacity-80">
      <div className="mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Menu Button */}
        <motion.button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          aria-label="Toggle Sidebar"
        >
          <MenuIcon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
        </motion.button>

        {/* Title */}
        <div className="flex-1 flex items-center justify-between">
          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-lg sm:text-xl font-semibold gradient-text hidden sm:block"
          >
            Chat
          </motion.h1>

          {/* User Menu */}
          <Menu as="div" className="relative">
            <MenuButton className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-semibold text-sm">
                <PersonIcon className="fill-white" size={20} />
              </div>
            </MenuButton>
            <MenuItems className="absolute right-0 mt-2 w-48 origin-top-right bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 focus:outline-none z-10">
              <MenuItem>
                {({ active }) => (
                  <button
                    className={`w-full text-left px-4 py-3 text-sm font-medium flex items-center gap-2 transition-colors ${
                      active ? "bg-gray-100 dark:bg-gray-700" : ""
                    }`}
                    onClick={handleLogout}
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                )}
              </MenuItem>
            </MenuItems>
          </Menu>
        </div>
      </div>
    </header>
  );
};
