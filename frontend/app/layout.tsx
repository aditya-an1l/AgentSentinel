import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentSentinel | Agent Tool Security",
  description: "Runtime screening and event visibility for AI-agent tool calls."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
