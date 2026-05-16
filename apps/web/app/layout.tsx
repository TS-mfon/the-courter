import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Courter",
  description: "Autonomous AI civil arbitration protocol on GenLayer",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg"
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
