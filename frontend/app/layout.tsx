import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Eye of Abyss — Cybercrime Intelligence Suite",
  description:
    "Converges voice deepfake detection, dark web attribution, and crypto forensics into tamper-proof case files.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
