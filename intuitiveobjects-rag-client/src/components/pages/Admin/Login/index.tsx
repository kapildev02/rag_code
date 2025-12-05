import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TextInput } from "@/components/atoms/TextInput";
import { Button } from "@/components/atoms/Button/Button";
import { useAppDispatch } from "@/store/hooks";
import {
	orgAdminLoginApi,
	registerOrganizationAdminApi,
	registerOrganizationAdminApiWithEmail,
	sendOtpApi,
	verifyOtpAndUpdateAdminApi,
} from "@/services/adminApi";
import useFormValidation from "@/hooks/useFormValidation";
import { validateAdminLoginForm } from "@/hooks/vaidate";
import toast from "react-hot-toast";
import { Settings, LogIn, Mail, Lock, Building2, Shield } from "lucide-react";
import { motion } from "framer-motion";

const initialLoginFormState = { email: "", password: "" };
const initialSignUpFormState = { organizationName: "", email: "" };

export const AdminLogin = () => {
	const dispatch = useAppDispatch();
	const navigate = useNavigate();
	const [isSignUp, setIsSignUp] = useState(false);
	const [loading, setLoading] = useState(false);
	const [showChangeCredentials, setShowChangeCredentials] = useState(false);
	const [changeForm, setChangeForm] = useState({
		organizationName: "",
		email: "",
	});
	const [otpSent, setOtpSent] = useState(false);
	const [otp, setOtp] = useState("");
	const [newPassword, setNewPassword] = useState("");
	const [newEmail, setNewEmail] = useState("");
	const [open, setOpen] = useState(false);

	const adminLoginForm = useFormValidation(initialLoginFormState, validateAdminLoginForm);
	const [signUpForm, setSignUpForm] = useState(initialSignUpFormState);

	const handleSignUpChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const { name, value } = e.target;
		setSignUpForm((prev) => ({ ...prev, [name]: value }));
	};

	const handleChangeForm = (e: React.ChangeEvent<HTMLInputElement>) => {
		const { name, value } = e.target;
		setChangeForm((prev) => ({ ...prev, [name]: value }));
	};

	const handleSignUp = async () => {
		if (!signUpForm.email || !signUpForm.organizationName) {
			toast.error("Please fill all fields");
			return;
		}
		setLoading(true);
		let res: any = null;
		try {
			res = await dispatch(
				registerOrganizationAdminApi({
					name: signUpForm.organizationName,
				})
			);
			if (res.type === "organization/register/fulfilled") {
				toast.success("Organization registered successfully.");
				setIsSignUp(false);
				setSignUpForm(initialSignUpFormState);
			} else {
				toast.error(res.payload?.response?.data?.message || "Registration failed");
			}
		} catch (err) {
			console.error(err);
			toast.error("Error occurred while registering.");
		} finally {
			setLoading(false);
		}
		if (res && res.payload && res.payload.data && res.payload.data.id) {
			setLoading(true);
			try {
				const response = await dispatch(
					registerOrganizationAdminApiWithEmail({
						organization_id: res.payload.data.id,
						name: signUpForm.organizationName,
						email: signUpForm.email,
						password: "epr_admin@123",
					})
				);
				if (response.type === "organization-admin/organizationadmin/fulfilled") {
					toast.success("Admin registered successfully!");
					setIsSignUp(false);
					setSignUpForm(initialSignUpFormState);
				} else {
					toast.error(response.payload?.response?.data?.message || "Registration failed");
				}
			} catch (err) {
				console.error(err);
				toast.error("Error occurred while registering with email.");
			} finally {
				setLoading(false);
			}
		}
	};

	const handleRequestOtp = async () => {
		if (!changeForm.organizationName || !changeForm.email) {
			toast.error("Please fill all fields");
			return;
		}
		setLoading(true);
		try {
			const res = await dispatch(
				sendOtpApi({
					organizationName: changeForm.organizationName,
					email: changeForm.email,
				})
			);
			if (res.type === "admin/sendOtp/fulfilled") {
				toast.success("OTP sent to your email.");
				setOtpSent(true);
			} else {
				toast.error("Failed to send OTP.");
			}
		} catch {
			toast.error("Error sending OTP.");
		} finally {
			setLoading(false);
		}
	};

	const handleVerifyOtpAndUpdate = async () => {
		if (!otp || !newPassword || !newEmail) {
			toast.error("Please fill all fields");
			return;
		}
		setLoading(true);
		try {
			const res = await dispatch(
				verifyOtpAndUpdateAdminApi({
					organizationName: changeForm.organizationName,
					email: changeForm.email,
					otp,
					newPassword,
					newEmail: newEmail || changeForm.email,
				})
			);
			if (res.type === "admin/verifyOtpAndUpdate/fulfilled") {
				toast.success("Credentials updated successfully!");
				setShowChangeCredentials(false);
				setOtpSent(false);
				setChangeForm({ organizationName: "", email: "" });
				setOtp("");
				setNewPassword("");
				setNewEmail("");
			} else {
				toast.error("Failed to update credentials.");
			}
		} catch {
			toast.error("Error updating credentials.");
		} finally {
			setLoading(false);
		}
	};

	const onSubmit = async () => {
		setLoading(true);
		try {
			const response = await dispatch(orgAdminLoginApi(adminLoginForm.values));
			if (response.type === "orgAdmin/login/fulfilled") {
				navigate("/admin");
				toast.success("Successfully logged in!");
			} else {
				toast.error(response.payload?.response?.data?.message || "Login failed");
			}
		} catch (err) {
			console.log(err);
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className="relative flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-white to-purple-50 dark:from-dark-bg dark:via-gray-900 dark:to-gray-800">
			{/* Animated background */}
			<div className="absolute inset-0 overflow-hidden">
				<div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-primary-500/15 to-accent-500/15 rounded-full blur-3xl animate-pulse" />
				<div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-tr from-primary-500/10 to-transparent rounded-full blur-3xl" />
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
						className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700"
					>
						<button
							onClick={() => navigate("/login")}
							className="block w-full px-6 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center gap-2"
						>
							<LogIn className="w-4 h-4" />
							Login as User
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
						<div className="flex justify-center mb-4">
							<div className="p-3 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-xl">
								<Shield className="w-8 h-8 text-primary-600 dark:text-primary-400" />
							</div>
						</div>
						<h1 className="text-3xl font-bold gradient-text mb-2">
							{isSignUp ? "Admin Sign Up" : showChangeCredentials ? "Reset Credentials" : "Admin Login"}
						</h1>
						<p className="text-gray-600 dark:text-gray-400">Manage your organization</p>
					</div>

					{/* Form */}
					{!isSignUp && !showChangeCredentials ? (
						<form
							onSubmit={(e) => {
								e.preventDefault();
								onSubmit();
							}}
							className="space-y-5"
						>
							<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
								<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Email
								</label>
								<div className="relative">
									<Mail className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
									<TextInput
										type="email"
										name="email"
										value={adminLoginForm.values.email}
										onChange={adminLoginForm.handleChange}
										placeholder="admin@company.com"
										error={adminLoginForm.errors.email}
										className="!pl-12"
									/>
								</div>
							</motion.div>

							<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
								<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Password
								</label>
								<div className="relative">
									<Lock className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
									<TextInput
										type="password"
										name="password"
										value={adminLoginForm.values.password}
										onChange={adminLoginForm.handleChange}
										error={adminLoginForm.errors.password}
										placeholder="••••••••"
										className="!pl-12"
									/>
								</div>
							</motion.div>

							<Button type="submit" disabled={loading} className="w-full btn-primary">
								{loading ? "Signing in..." : "Sign In"}
							</Button>

							<div className="space-y-2 text-center text-sm">
								<p className="text-gray-600 dark:text-gray-400">
									New Admin?{" "}
									<button
										type="button"
										onClick={() => setIsSignUp(true)}
										className="font-semibold text-primary-500 hover:text-primary-600"
									>
										Sign up here
									</button>
								</p>
								<button
									type="button"
									onClick={() => setShowChangeCredentials(true)}
									className="text-primary-500 hover:text-primary-600 font-medium"
								>
									Reset Email/Password?
								</button>
							</div>
						</form>
					) : showChangeCredentials ? (
						<div className="space-y-5">
							{!otpSent ? (
								<>
									<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											Organization Name
										</label>
										<div className="relative">
											<Building2 className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
											<TextInput
												type="text"
												name="organizationName"
												value={changeForm.organizationName}
												onChange={handleChangeForm}
												placeholder="Your Organization"
												className="!pl-12"
											/>
										</div>
									</motion.div>

									<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											Current Email
										</label>
										<div className="relative">
											<Mail className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
											<TextInput
												type="email"
												name="email"
												value={changeForm.email}
												onChange={handleChangeForm}
												placeholder="your@email.com"
												className="!pl-12"
											/>
										</div>
									</motion.div>

									<Button onClick={handleRequestOtp} disabled={loading} className="w-full btn-primary">
										{loading ? "Sending..." : "Send OTP"}
									</Button>

									<button
										type="button"
										onClick={() => setShowChangeCredentials(false)}
										className="w-full text-primary-500 hover:text-primary-600 font-medium"
									>
										Back to Login
									</button>
								</>
							) : (
								<>
									<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											OTP
										</label>
										<TextInput
											type="text"
											value={otp}
											onChange={(e) => setOtp(e.target.value)}
											placeholder="000000"
										/>
									</motion.div>

									<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											New Email (optional)
										</label>
										<div className="relative">
											<Mail className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
											<TextInput
												type="email"
												value={newEmail}
												onChange={(e) => setNewEmail(e.target.value)}
												placeholder="newemail@company.com"
												className="!pl-12"
											/>
										</div>
									</motion.div>

									<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											New Password
										</label>
										<div className="relative">
											<Lock className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
											<TextInput
												type="password"
												value={newPassword}
												onChange={(e) => setNewPassword(e.target.value)}
												placeholder="••••••••"
												className="!pl-12"
											/>
										</div>
									</motion.div>

									<Button onClick={handleVerifyOtpAndUpdate} disabled={loading} className="w-full btn-primary">
										{loading ? "Updating..." : "Update Credentials"}
									</Button>

									<button
										type="button"
										onClick={() => {
											setOtpSent(false);
											setOtp("");
										}}
										className="w-full text-primary-500 hover:text-primary-600 font-medium"
									>
										Back
									</button>
								</>
							)}
						</div>
					) : (
						<div className="space-y-5">
							<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
								<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Organization Name
								</label>
								<div className="relative">
									<Building2 className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
									<TextInput
										type="text"
										name="organizationName"
										value={signUpForm.organizationName}
										onChange={handleSignUpChange}
										placeholder="Your Organization"
										className="!pl-12"
									/>
								</div>
							</motion.div>

							<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
								<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Email
								</label>
								<div className="relative">
									<Mail className="absolute left-4 top-3 w-5 h-5 text-gray-400" />
									<TextInput
										type="email"
										name="email"
										value={signUpForm.email}
										onChange={handleSignUpChange}
										placeholder="admin@company.com"
										className="!pl-12"
									/>
								</div>
							</motion.div>

							<Button onClick={handleSignUp} disabled={loading} className="w-full btn-primary">
								{loading ? "Creating account..." : "Create Account"}
							</Button>

							<p className="text-center text-sm text-gray-600 dark:text-gray-400">
								Already have an account?{" "}
								<button
									type="button"
									onClick={() => setIsSignUp(false)}
									className="font-semibold text-primary-500 hover:text-primary-600"
								>
									Login here
								</button>
							</p>
						</div>
					)}
				</div>
			</motion.div>
		</div>
	);
};

