import Footer from "@/components/footer";
import "@/styles/globals.css";
import type { AppProps } from "next/app";
import Navbar from "../components/navBar";
import { ChakraProvider } from "@chakra-ui/react";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <ChakraProvider>
        <Navbar />
        <Component {...pageProps} />
        <Footer />
      </ChakraProvider>
    </>
  );
}
