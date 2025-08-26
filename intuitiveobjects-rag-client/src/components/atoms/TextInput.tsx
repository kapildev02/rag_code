import React, { ChangeEvent, useState } from "react";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  type?: string;
  error?: string;
  label?: string;
  value?: string;
  placeholder?: string;
  name?: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  hideLabel?: boolean;
  toggleColor?: string; // Add toggleColor prop
}

export const TextInput: React.FC<TextInputProps> = ({
  type = "text",
  error,
  label,
  value,
  placeholder,
  onChange,
  hideLabel = false,
  className,
  toggleColor = "#9CA3AF", // default gray-400
  ...props
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;

  return (
    <div className="relative">
      {!hideLabel && (
        <label className="block text-sm font-medium text-gray-400 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          type={inputType}
          value={value}
          placeholder={placeholder}
          onChange={onChange}
          className={`w-full bg-chat-bg border border-chat-border rounded-md px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-chat-border ${className} ${isPassword ? "pr-10" : ""}`}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            tabIndex={-1}
            className="absolute right-3 inset-y-0 my-auto flex items-center h-5"
            onClick={() => setShowPassword((v) => !v)}
            style={{ color: toggleColor }}
          >
            {showPassword ? (
              // Eye open SVG
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            ) : (
              // Eye closed SVG
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.956 9.956 0 012.293-3.95M6.634 6.634A9.956 9.956 0 0112 5c4.478 0 8.268 2.943 9.542 7a9.956 9.956 0 01-4.293 5.95M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" />
              </svg>
            )}
          </button>
        )}
      </div>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
};