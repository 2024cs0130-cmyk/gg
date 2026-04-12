import type { Metadata, Viewport } from "next";
import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/600.css";
import "@fontsource/geist-sans/700.css";
import "@fontsource/geist-mono/400.css";
import "@fontsource/geist-mono/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevIQ — Developer Intelligence",
  description:
    "Advanced developer analytics platform for engineering teams. Real-time insights, performance metrics, and commitment intelligence.",
  keywords: [
    "developer analytics",
    "engineering metrics",
    "team performance",
    "code quality",
    "developer intelligence",
  ],
  authors: [{ name: "DevIQ Team" }],
  creator: "DevIQ",
  publisher: "DevIQ",
  formatDetection: {
    email: false,
    telephone: false,
    address: false,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://deviq.app",
    title: "DevIQ — Developer Intelligence",
    description:
      "Advanced developer analytics platform for engineering teams. Real-time insights, performance metrics, and commitment intelligence.",
    siteName: "DevIQ",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "DevIQ",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "DevIQ — Developer Intelligence",
    description:
      "Advanced developer analytics platform for engineering teams. Real-time insights, performance metrics, and commitment intelligence.",
    images: ["/twitter-image.png"],
    creator: "@deviqapp",
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
    },
  },
  alternates: {
    canonical: "https://deviq.app",
  },
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#6366f1",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
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
    >
      <head>
        {/* Prevent flash of unstyled content */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const isDark = localStorage.getItem('theme') === 'dark' || 
                    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
                  if (isDark) {
                    document.documentElement.style.colorScheme = 'dark';
                  }
                } catch (e) {}
              })()
            `,
          }}
        />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes, viewport-fit=cover"
        />
        <meta name="color-scheme" content="dark" />
        <meta name="theme-color" content="#0a0a0a" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="#fafafa" media="(prefers-color-scheme: light)" />
        <meta name="msapplication-TileColor" content="#0a0a0a" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
