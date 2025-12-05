/** @type {import('tailwindcss').Config} */
export default {
	content: [
		"./src/components/**/*.{js,jsx,ts,tsx}",
		"./src/atoms/**/*.{js,jsx,ts,tsx}",
		"./src/molecules/**/*.{js,jsx,ts,tsx}",
		"./src/organisms/**/*.{js,jsx,ts,tsx}",
		"./src/templates/**/*.{js,jsx,ts,tsx}",
		"./src/pages/**/*.{js,jsx,ts,tsx}",
		"./index.html",
	],
	theme: {
		extend: {
			colors: {
				primary: {
					50: "#f0ebff",
					100: "#1f2937",
					200: "#1f2937",
					300: "#b88aff",
					400: "#9d61ff",
					500: "#6C63FF",
					600: "#5a52d5",
					700: "#4840aa",
					800: "#362f7f",
					900: "#241d54",
				},
				accent: {
					50: "#e8fdf9",
					100: "#c7fcf0",
					200: "#8ff8e1",
					300: "#57f4d2",
					400: "#1ef0c3",
					500: "#00D2A8",
					600: "#00a888",
					700: "#007e68",
					800: "#005448",
					900: "#002a28",
				},
				background: "#1f2937",
				"dark-bg": "#0f0f1e",
				"card-bg": "rgba(255, 255, 255, 0.05)",
			},
			fontFamily: {
				sans: ["Inter", "Plus Jakarta Sans", "system-ui", "sans-serif"],
			},
			animation: {
				fadeIn: "fadeIn 0.3s ease-in-out",
				slideUp: "slideUp 0.3s ease-out",
				scaleIn: "scaleIn 0.3s ease-out",
			},
			keyframes: {
				fadeIn: {
					"0%": { opacity: "0" },
					"100%": { opacity: "1" },
				},
				slideUp: {
					"0%": { transform: "translateY(10px)", opacity: "0" },
					"100%": { transform: "translateY(0)", opacity: "1" },
				},
				scaleIn: {
					"0%": { transform: "scale(0.95)", opacity: "0" },
					"100%": { transform: "scale(1)", opacity: "1" },
				},
			},
		},
	},
	plugins: [],
};
