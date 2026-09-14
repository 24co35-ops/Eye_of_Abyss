import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Eye of Abyss — Cybercrime Intelligence Suite",
  description:
    "Converges voice deepfake detection, dark web attribution, and crypto forensics into tamper-proof case files.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        {children}
      </body>
    </html>
  );
}
