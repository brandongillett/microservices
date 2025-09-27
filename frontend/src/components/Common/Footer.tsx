import { Box, Container, HStack, Text, VStack } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { tokens } from "@/tokens/getTokens";

export function Footer() {
	const { color: colors } = tokens;

	const fonts = {
		body: "GeneralSans, sans-serif",
	};

	return (
		<Box
			bg={colors.background.default}
			borderTop="1px solid"
			borderColor={colors.border.default}
			py={12}
			mt={20}
		>
			<Container maxW="6xl">
				<VStack gap={6}>
					{/* Ready to Match Section */}
					<VStack gap={4}>
						<Text
							fontSize={{ base: "xl", md: "2xl" }}
							fontWeight="semibold"
							color={colors.foreground.default}
							textAlign="center"
							fontFamily={fonts.body}
						>
							Ready to Build{" "}
							<Text as="span" color={colors.brand.primary}>
								Microservices
							</Text>
							?
						</Text>
					</VStack>

					{/* Links */}
					<HStack gap={1} flexWrap="wrap" justifyContent="center">
						<Link to="/privacy">
							<Text
								color={colors.foreground.muted}
								fontSize="sm"
								fontFamily={fonts.body}
								_hover={{
									color: colors.brand.primary,
								}}
								cursor="pointer"
								transition="color 0.2s ease"
							>
								Privacy Policy
							</Text>
						</Link>
						<Text color={colors.foreground.muted} fontSize="sm" mx={2}>|</Text>
						<Link to="/terms">
							<Text
								color={colors.foreground.muted}
								fontSize="sm"
								fontFamily={fonts.body}
								_hover={{
									color: colors.brand.primary,
								}}
								cursor="pointer"
								transition="color 0.2s ease"
							>
								Terms of Service
							</Text>
						</Link>
						<Text color={colors.foreground.muted} fontSize="sm" mx={2}>|</Text>
						<Link to="/contact">
							<Text
								color={colors.foreground.muted}
								fontSize="sm"
								fontFamily={fonts.body}
								_hover={{
									color: colors.brand.primary,
								}}
								cursor="pointer"
								transition="color 0.2s ease"
							>
								Contact Us
							</Text>
						</Link>
					</HStack>

					{/* Copyright */}
					<Text
						color={colors.foreground.muted}
						fontSize="sm"
						textAlign="center"
						fontFamily={fonts.body}
					>
						© 2025 Copyright. All rights reserved.
					</Text>
				</VStack>
			</Container>
		</Box>
	);
}
