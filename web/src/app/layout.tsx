import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MagicStream - Cinematic Experience",
  description: "A magical streaming experience for movie lovers.",
};

import { Navbar } from "@/components/navbar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${inter.variable} ${playfair.variable} antialiased bg-midnight-950 text-white selection:bg-gold-500/30 overflow-x-hidden`}
      >
        <Navbar />
        <main className="min-h-screen pt-16">
          {children}
        </main>
        <footer className="py-8 bg-midnight-950 border-t border-white/5 text-center text-slate-500 text-sm">
          <p>© {new Date().getFullYear()} MagicStream. Powered by MovieLens Data.</p>
        </footer>
      </body>
    </html>
  );
}
