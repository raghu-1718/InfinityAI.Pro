import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { useEffect, useState } from "react";
import { checkFrontendEnvVars } from "@/lib/envCheck";
import { EnvErrorBanner } from "@/components/EnvErrorBanner";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "InfinityAI.Pro - AI-Powered Trading Platform",
  description: "Real-time AI-powered trading analytics, risk management, and execution platform",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Fail-fast env check (client only)
  const [missing, setMissing] = useState<string[]>([]);
  useEffect(() => {
    setMissing(checkFrontendEnvVars());
  }, []);
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <EnvErrorBanner missing={missing} />
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
