import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router";
import React, { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { routeTree } from "./routeTree.gen";

import "./styles/fonts.css";
import { ChakraProvider } from "@chakra-ui/react";
import { system } from "./theme";
import { Toaster } from "./components/ui/toaster";

const queryClient = new QueryClient()

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ChakraProvider value={system}>
            <QueryClientProvider client={queryClient}>
                <RouterProvider router={router} />
                <Toaster />
            </QueryClientProvider>
        </ChakraProvider>
    </StrictMode>,
);
