import { Box, Container, Flex, HStack, Text, VStack, IconButton } from "@chakra-ui/react";
import { Link } from "@tanstack/react-router";
import { FiHome, FiMenu, FiX, FiFileText, FiStar } from "react-icons/fi";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { tokens } from "@/tokens/getTokens";

// Use your actual design tokens!
const { color: colors } = tokens;

function Navbar() {
	const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
	const navItems = [
		{ label: "Home", href: "/", icon: <FiHome /> },
	];

	return (
		<Box
			position="sticky"
			top={0}
			zIndex="sticky"
			bg={colors.background.default}
			borderBottom="1px"
			borderColor={colors.border.default}
			backdropFilter="blur(10px)"
			backdropSaturate="180%"
		>
			<Container maxW="7xl" px={{ base: 4, md: 6 }}>
				<Flex align="center" justify="space-between" h="20">
					{/* Logo */}
					<Link to="/">
						<HStack gap={2}>
							<Text
								fontSize="3xl"
								fontWeight="bold"
								color={colors.foreground.default}
								fontFamily="GeneralSans"
							>
								Microservices
							</Text>
						</HStack>
					</Link>

					{/* Desktop Navigation Menu */}
					<HStack gap={3} display={{ base: "none", md: "flex" }}>
						{navItems.map((item) => (
							<Link key={item.href} to={item.href}>
								<Button
									variant="ghost"
									size="sm"
									color={colors.foreground.muted}
									_hover={{
										bg: colors.background.muted,
										color: colors.foreground.default,
									}}
									transition="all 0.2s ease"
								>
									<HStack gap={2}>
										{item.icon}
										<Text fontWeight="medium">{item.label}</Text>
									</HStack>
								</Button>
							</Link>
						))}
					</HStack>

					{/* Mobile Menu Button */}
					<IconButton
						aria-label="Toggle mobile menu"
						display={{ base: "flex", md: "none" }}
						variant="ghost"
						color={colors.foreground.default}
						onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
						_hover={{
							bg: colors.background.muted,
						}}
					>
						{isMobileMenuOpen ? <FiX /> : <FiMenu />}
					</IconButton>
				</Flex>

				{/* Mobile Menu */}
				{isMobileMenuOpen && (
					<Box
						display={{ base: "block", md: "none" }}
						pb={4}
						borderBottom="1px"
						borderColor={colors.border.default}
					>
						<VStack gap={2} align="stretch">
							{navItems.map((item) => (
								<Link key={item.href} to={item.href}>
									<Button
										variant="ghost"
										size="md"
										color={colors.foreground.muted}
										_hover={{
											bg: colors.background.muted,
											color: colors.foreground.default,
										}}
										transition="all 0.2s ease"
										w="full"
										justifyContent="flex-start"
										onClick={() => setIsMobileMenuOpen(false)}
									>
										<HStack gap={2}>
											{item.icon}
											<Text fontWeight="medium">{item.label}</Text>
										</HStack>
									</Button>
								</Link>
							))}
						</VStack>
					</Box>
				)}
			</Container>
		</Box>
	);
}

export default Navbar;
