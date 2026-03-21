import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/src/components/Navbar";


export const metadata: Metadata = {
  title: "Prompt Refiner",
  description: "Agentic AI Prompt Refiner",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <Navbar />
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
