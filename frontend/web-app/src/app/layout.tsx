import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex flex-1 flex-col pl-64 transition-all duration-300 data-[sidebar-collapsed=true]:pl-16">
              <Header />
              <main className="flex-1 bg-muted/30">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
