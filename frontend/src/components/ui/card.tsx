import { Box, VStack, BoxProps } from "@chakra-ui/react";
import { ReactNode } from "react";
import { tokens } from "../../tokens/getTokens";

interface CardProps extends BoxProps {
    children: ReactNode;
    accentColor?: string;
    size?: "md" | "lg";
}

export function Card({
    children,
    accentColor,
    size = "lg",
    ...boxProps
}: CardProps) {
    const { color: colors } = tokens;
    const cardAccentColor = accentColor || colors.brand.primary;

    return (
        <Box
            position="relative"
            overflow="hidden"
            border="2px solid"
            borderColor="transparent"
            bg={`linear-gradient(135deg, ${cardAccentColor}08, ${colors.background.elevated})`}
            borderRadius="xl"
            p={size === "lg" ? 6 : 4}
            _hover={{
                borderColor: colors.brand.primary,
                transform: "translateY(-6px)",
                boxShadow: `0 25px 50px ${colors.brand.primary}15, 0 0 0 1px ${colors.brand.primary}20`,
                bg: `linear-gradient(135deg, ${cardAccentColor}12, ${colors.background.elevated})`,
            }}
            transition="all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
            _before={{
                content: '""',
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                height: "3px",
                background: `linear-gradient(90deg, ${cardAccentColor}, ${cardAccentColor}60, transparent)`,
                opacity: 0.8,
            }}
            {...boxProps}
        >
            <VStack gap={6} align="start" position="relative" zIndex={1}>
                {children}
            </VStack>
        </Box>
    );
}
