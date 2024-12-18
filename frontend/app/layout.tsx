import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "My Webapp!",
  description: "This is my webapp!",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
