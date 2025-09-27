import { createSystem, defaultConfig } from "@chakra-ui/react";
import { tokens } from "./tokens/getTokens";

export const system = createSystem(defaultConfig, {
	globalCss: {
		html: {
			fontSize: "16px",
			fontFamily: tokens.typography.fonts.brand.family,
			scrollBehavior: "smooth",
		},
		body: {
			backgroundColor: tokens.color.background.default,
			color: tokens.color.foreground.default,
			fontSize: "16px",
			fontFamily: tokens.typography.fonts.brand.family,
			margin: 0,
			padding: 0,
			lineHeight: 1.5,
			minHeight: "100vh",
			overflowX: "hidden",
		},
		"#root": {
			minHeight: "100vh",
			display: "flex",
			flexDirection: "column",
		},
		"*": {
			borderColor: tokens.color.background.muted,
			boxSizing: "border-box",
		},
		"::selection": {
			backgroundColor: tokens.color.brand.primary,
			color: tokens.color.foreground.onAccent,
		},
		".main-link": {
			color: tokens.color.brand.primary,
			fontWeight: "600",
			textDecoration: "none",
			transition: "color 250ms ease",
			_hover: {
				color: tokens.color.brand.primaryLight,
				textDecoration: "underline",
			},
		},
	},
	theme: {
		recipes: {
		},
	},
});
