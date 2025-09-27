import { Button } from "@/components/ui/button";
import {
	Box,
	Container,
	VStack,
	HStack,
	Text,
	Flex
} from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { FiHome } from "react-icons/fi";
import { tokens } from "@/tokens/getTokens";

const NotFound = () => {
	const { color: colors, semantic } = tokens;

	const fonts = {
		heading: "GeneralSans, sans-serif",
		body: "GeneralSans, sans-serif",
	};

	return (
		<Box
			bg={colors.background.default}
			minH="100vh"
			position="relative"
			overflow="hidden"
		>
			{/* Animated Background Elements */}
			<Box
				position="absolute"
				top="10%"
				left="10%"
				width="300px"
				height="300px"
				bg={`linear-gradient(135deg, ${colors.brand.primary}15, transparent)`}
				borderRadius="full"
				filter="blur(40px)"
				css={{
					animation: "float 6s ease-in-out infinite",
					"@keyframes float": {
						"0%, 100%": { transform: "translateY(0px)" },
						"50%": { transform: "translateY(-20px)" },
					},
				}}
			/>
			<Box
				position="absolute"
				bottom="20%"
				right="15%"
				width="200px"
				height="200px"
				bg={`linear-gradient(135deg, ${colors.brand.primary}10, transparent)`}
				borderRadius="full"
				filter="blur(30px)"
				css={{
					animation: "float 8s ease-in-out infinite reverse",
				}}
			/>

			<Container maxW="4xl" py={20}>
				<Flex
					height="80vh"
					align="center"
					justify="center"
					flexDir="column"
					data-testid="not-found"
					position="relative"
					zIndex={2}
				>
					{/* Centered 404 Message */}
					<VStack gap={8} textAlign="center" maxW="600px">
						{/* 404 Number with Gradient */}
						<Box position="relative">
							<Text
								fontSize={{ base: "8xl", md: "9xl", lg: "10xl" }}
								fontWeight="bold"
								lineHeight="0.8"
								fontFamily={fonts.heading}
								background={`linear-gradient(135deg, ${colors.brand.primary}, ${colors.brand.primary}80)`}
								backgroundClip="text"
								color="transparent"
								textShadow={`0 0 40px ${colors.brand.primary}30`}
								position="relative"
								_before={{
									content: '"404"',
									position: "absolute",
									top: "4px",
									left: "4px",
									background: `linear-gradient(135deg, ${colors.brand.primary}20, ${colors.brand.primary}10)`,
									backgroundClip: "text",
									color: "transparent",
									zIndex: -1,
								}}
							>
								404
							</Text>
						</Box>

						{/* Title and Description */}
						<VStack gap={4}>
							<Text
								fontSize={{ base: "2xl", md: "3xl" }}
								fontWeight="bold"
								color={colors.foreground.default}
								fontFamily={fonts.heading}
							>
								Looks like you're lost in space
							</Text>
							<Text
								fontSize={{ base: "lg", md: "xl" }}
								color={colors.foreground.muted}
								fontFamily={fonts.body}
								lineHeight="tall"
								maxW="400px"
							>
								The page you're looking for doesn't exist. Don't worry, even the best explorers get lost sometimes!
							</Text>
						</VStack>

						{/* Go Home Button */}
						<Box pt={4}>
							<Link to="/">
								<Button
									size="lg"
									bg={semantic.button.primary.bg.default}
									color={semantic.button.primary.fg.default}
									px={8}
									py={6}
									fontSize="md"
									fontWeight="semibold"
									borderRadius="xl"
									_hover={{
										bg: semantic.button.primary.bg.hover,
										transform: "translateY(-2px)",
										boxShadow: `0 12px 30px ${colors.brand.primary}40`,
									}}
									transition="all 0.3s ease"
								>
									<HStack gap={2}>
										<FiHome />
										<Text>Go Home</Text>
									</HStack>
								</Button>
							</Link>
						</Box>
					</VStack>
				</Flex>
			</Container>
		</Box>
	);
};

export default NotFound;
