import { useNavigate } from "react-router-dom";
import { useAppDispatch } from "@/store/hooks";
import { Button } from "@/components/atoms/Button/Button";
import { TextInput } from "@/components/atoms/TextInput";
import useFormValidation from "@/hooks/useFormValidation";
import { authUserLoginApi } from "@/services/authApi";
import { validateUserLoginForm } from "@/hooks/vaidate";
import { showError, showSuccess } from "@/utils/sweetAlert";
import { Settings, LogIn, Mail, Lock } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const initialState = {
	email: "",
	password: "",
};

const Login = () => {
	const dispatch = useAppDispatch();
	const navigate = useNavigate();
	const loginForm = useFormValidation(initialState, validateUserLoginForm);
	const [open, setOpen] = useState(false);

	const onSubmit = async () => {
		const response = await dispatch(authUserLoginApi(loginForm.values));
		if (response.type === "auth/user/login/fulfilled") {
			navigate("/");
			showSuccess("Login successful");
		}
		if (response.type === "auth/user/login/rejected") {
			showError(response.payload.response.data.message);
		}
	};

	return (
		<div className="relative flex min-h-screen items-center justify-center bg-[#1f2937] dark:bg-gray-900">
			{/* Animated background gradient */}
			<div className="absolute inset-0 overflow-hidden">
				<div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-primary-500/10 to-accent-500/10 rounded-full blur-3xl animate-pulse" />
				<div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-primary-500/5 to-transparent rounded-full blur-3xl" />
			</div>

			{/* Settings Icon */}
			<div className="absolute top-8 right-8 z-10">
				<motion.button
					onClick={() => setOpen(!open)}
					className="p-2.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
					whileHover={{ scale: 1.1 }}
					whileTap={{ scale: 0.95 }}
				>
					<Settings className="w-6 h-6 text-gray-700 dark:text-gray-300" />
				</motion.button>

				{open && (
					<motion.div
						initial={{ opacity: 0, y: -10 }}
						animate={{ opacity: 1, y: 0 }}
						exit={{ opacity: 0, y: -10 }}
						className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
					>
						<button
							onClick={() => navigate("/admin/login")}
							className="block w-full px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center gap-2"
						>
							<LogIn className="w-4 h-4" />
							Login as Admin
						</button>
					</motion.div>
				)}
			</div>

			{/* Login Card */}
			<motion.div
				initial={{ opacity: 0, y: 20 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 0.5 }}
				className="relative w-full max-w-md px-4 z-10"
			>
				<div className="glass-card">
					{/* Header */}
					<div className="text-center mb-8">
						<h1 className="text-3xl font-bold gradient-text mb-2">
							Welcome Back
						</h1>
						<p className="text-gray-600 dark:text-gray-400">
							Sign in to your account
						</p>
					</div>

					{/* Form */}
					<form
						onSubmit={(e) => {
							e.preventDefault();
							loginForm.handleSubmit(onSubmit);
						}}
						className="space-y-5"
					>
						{/* Email Field */}
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							transition={{ delay: 0.1 }}
						>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Email Address
							</label>
							<div className="relative">
								<Mail className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
								<TextInput
									type="email"
									placeholder="you@example.com"
									name="email"
									onChange={loginForm.handleChange}
									error={loginForm.errors.email}
									className="!pl-12"
								/>
							</div>
						</motion.div>

						{/* Password Field */}
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							transition={{ delay: 0.2 }}
						>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Password
							</label>
							<div className="relative">
								<Lock className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
								<TextInput
									type="password"
									placeholder="••••••••"
									name="password"
									onChange={loginForm.handleChange}
									error={loginForm.errors.password}
									className="!pl-12"
								/>
							</div>
						</motion.div>

						{/* Submit Button */}
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							transition={{ delay: 0.3 }}
						>
							<Button className="w-full btn-primary" type="submit">
								Sign In
							</Button>
						</motion.div>
					</form>
				</div>

				{/* Footer */}
				<div className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
					Don't have an account?{" "}
					<a
						href="#"
						className="font-semibold text-primary-500 hover:text-primary-600"
					>
						Contact Admin
					</a>
				</div>
			</motion.div>
		</div>
	);
};

export default Login;
