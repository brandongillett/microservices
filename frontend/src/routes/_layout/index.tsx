import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Footer } from "@/components/Common/Footer";
import { TypewriterText } from "@/components/Common/TypewriterText";
import {
	Box,
	Container,
	HStack,
	SimpleGrid,
	Text,
	VStack,
} from "@chakra-ui/react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { FiClock, FiCalendar, FiKey } from "react-icons/fi";

import { tokens } from "@/tokens/getTokens";

export const Route = createFileRoute("/_layout/")({
	component: LandingPage,
});

function LandingPage() {
	const { color: colors, semantic } = tokens;

	const fonts = {
		heading: "GeneralSans, sans-serif",
		body: "GeneralSans, sans-serif",
	};

	const features = [
		{
			icon: <FiClock />,
			title: "Fully Asynchronous",
			description: "Scale and perform with async-first architecture.",
			color: colors.brand.primary,
		},
		{
			icon: <FiCalendar />,
			title: "Event Driven Architecture",
			description: "Decoupled services and boost responsiveness with events using a message broker.",
			color: "#8B5CF6",
		},
		{
			icon: <FiKey />,
			title: "Design Tokens",
			description: "Consistent theming and styling with design tokens.",
			color: "#F59E0B",
		},
	];

	return (
		<Box bg={colors.background.default} minH="100vh">
			{/* Hero Section */}
			<Container maxW="6xl" py={{ base: 20, md: 32 }}>
				<VStack gap={12} textAlign="center" mb={20}>
					<VStack gap={6}>
						<TypewriterText
							text="Build Microservices"
							brandStartIndex={5} // When to use brand color
							fontSize={{ base: "5xl", md: "7xl", lg: "8xl" }}
							fontWeight="bold"
							lineHeight="shorter"
							fontFamily={fonts.heading}
						/>
						<Text
							fontSize={{ base: "xl", md: "2xl" }}
							color={colors.foreground.muted}
							maxW="3xl"
							mx="auto"
							lineHeight="tall"
							fontFamily={fonts.body}
						>
							FastAPI Microservice Boilerplate to kickstart your next project
						</Text>
					</VStack>

					<HStack gap={6} flexWrap="wrap" justifyContent="center">
						<Link to="/login">
							<Button
								size="lg"
								bg={semantic.button.primary.bg.default}
								color={semantic.button.primary.fg.default}
								px={10}
								py={7}
								fontSize="lg"
								fontWeight="semibold"
								borderRadius="xl"
								_hover={{
									bg: semantic.button.primary.bg.hover,
									transform: "translateY(-2px)",
									boxShadow: `0 12px 30px ${colors.brand.primary}40`,
								}}
								transition="all 0.3s ease"
							>
								Login
							</Button>
						</Link>
						<Link to="/register">
							<Button
								size="lg"
								variant="outline"
								borderColor={colors.brand.primary}
								color={colors.brand.primary}
								bg="transparent"
								px={10}
								py={7}
								fontSize="lg"
								fontWeight="semibold"
								borderRadius="xl"
								_hover={{
									bg: colors.brand.primary + "10",
									borderColor: colors.brand.primary,
									transform: "translateY(-1px)",
								}}
								transition="all 0.3s ease"
							>
								Register
							</Button>
						</Link>
					</HStack>
				</VStack>

				{/* Features Section */}
				<VStack gap={12}>
					<SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={8} w="full">
						{features.map((feature) => (
							<Card
								key={feature.title}
								size="lg"
								accentColor={feature.color}
							>
								<VStack gap={6} align="start">
									{/* Icon Container */}
									<Box
										p={5}
										borderRadius="xl"
										bg={`linear-gradient(135deg, ${feature.color}15, ${feature.color}08)`}
										border="2px solid"
										borderColor={`${feature.color}25`}
										color={feature.color}
										fontSize="3xl"
										display="flex"
										alignItems="center"
										justifyContent="center"
										w="20"
										h="20"
										_hover={{
											borderColor: feature.color,
											transform: "scale(1.08)",
											boxShadow: `0 12px 30px ${feature.color}30`,
											bg: `linear-gradient(135deg, ${feature.color}25, ${feature.color}15)`,
										}}
										transition="all 0.3s ease"
									>
										{feature.icon}
									</Box>

									{/* Content */}
									<Box w="full">
										<Text
											fontSize="xl"
											fontWeight="bold"
											mb={3}
											color={colors.foreground.default}
											fontFamily={fonts.heading}
											position="relative"
										>
											{feature.title}
											<Box
												position="absolute"
												bottom="-4px"
												left={0}
												width="30px"
												height="3px"
												bg={feature.color}
												borderRadius="full"
											/>
										</Text>
										<Text
											color={colors.foreground.muted}
											lineHeight="tall"
											fontFamily={fonts.body}
											fontSize="md"
										>
											{feature.description}
										</Text>
									</Box>
								</VStack>
							</Card>
						))}
					</SimpleGrid>
				</VStack>
			</Container>
			<Footer />
		</Box>
	);
}
