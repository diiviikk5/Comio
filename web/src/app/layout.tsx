import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "COMIO — The Comic Reader That Sets Your Collection Free",
  description:
    "A premium desktop comic reader with Internet Archive integration. Read 10,000+ free public domain comics. Supports CBR, CBZ, ZIP, RAR. Available for Windows, macOS, and Linux.",
  keywords: ["comic reader", "CBR", "CBZ", "Internet Archive", "free comics", "desktop app"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
