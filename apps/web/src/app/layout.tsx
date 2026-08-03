import type { Metadata } from "next";
import { Suspense } from "react";
import { AppShell } from "@/components/AppShell";
import { AuthGate } from "@/components/AuthGate";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AdzMate — Campaign Auto-Pilot",
  description: "Enterprise multi-agent marketing automation for IDEALIZE 2026",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <AuthProvider>
          <AuthGate>
            <Suspense fallback={null}>
              <AppShell>{children}</AppShell>
            </Suspense>
          </AuthGate>
        </AuthProvider>
      </body>
    </html>
  );
}
