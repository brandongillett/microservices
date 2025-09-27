import { Box, VStack, BoxProps } from "@chakra-ui/react";
import { ReactNode } from "react";
import { tokens } from "../../tokens/getTokens";

interface FormProps extends BoxProps {
	children: ReactNode;
}

export function Form({ children, ...boxProps }: FormProps) {
	const { color: colors } = tokens;

	return (
		<Box
			mx="auto"
			p={8}
			borderRadius="2xl"
			bg={`linear-gradient(135deg, ${colors.brand.primary}08, ${colors.background.elevated})`}
			border="2px solid"
			borderColor="transparent"
			boxShadow="0 20px 40px rgba(0, 0, 0, 0.1)"
			position="relative"
			overflow="hidden"
			_before={{
				content: '""',
				position: "absolute",
				top: 0,
				left: 0,
				right: 0,
				height: "3px",
				background: `linear-gradient(90deg, ${colors.brand.primary}, ${colors.brand.primary}60, transparent)`,
				opacity: 0.8,
			}}
			{...boxProps}
		>
			<VStack gap={6} align="stretch">
				{children}
			</VStack>
		</Box>
	);
}
