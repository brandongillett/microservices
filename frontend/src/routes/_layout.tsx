import Navbar from "@/components/Common/Navbar";
import { Flex } from "@chakra-ui/react";
import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout")({
	component: Layout,
});

function Layout() {
	return (
		<Flex direction="column" h="100vh">
			<Navbar />
			<Flex flex="1" overflow="hidden">
				<Flex flex="1" direction="column" overflowY="auto">
					<Outlet />
				</Flex>
			</Flex>
		</Flex>
	);
}

export default Layout;
