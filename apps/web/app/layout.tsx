import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "FlowSync Revenue Intelligence",
    template: "%s | FlowSync BI",
  },
  description:
    "Production-grade SaaS Revenue Intelligence Dashboard for FlowSync — track MRR, ARR, NRR, cohort retention, customer health, and funnel analytics.",
  keywords: [
    "SaaS metrics",
    "revenue intelligence",
    "MRR",
    "ARR",
    "NRR",
    "churn analysis",
    "cohort retention",
    "customer health",
    "business intelligence",
    "FlowSync",
  ],
  authors: [{ name: "FlowSync Engineering" }],
  creator: "FlowSync",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://flowsync-bi.vercel.app",
    title: "FlowSync Revenue Intelligence",
    description: "Enterprise-grade SaaS analytics platform",
    siteName: "FlowSync BI",
  },
  twitter: {
    card: "summary_large_image",
    title: "FlowSync Revenue Intelligence",
    description: "Enterprise-grade SaaS analytics platform",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f8fafc" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0f1e" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
