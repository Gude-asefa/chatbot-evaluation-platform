import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chatbot Evaluation Platform · Bank of Abyssinia",
  description: "Internal chatbot pilot testing platform",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <div className="topbar-inner">
            <span className="brand-mark" aria-hidden>BoA</span>
            <span className="brand-name">Bank of Abyssinia</span>
            <span className="brand-sep" aria-hidden>|</span>
            <span className="brand-app">Chatbot pilot testing</span>
          </div>
        </header>
        <main className="container">{children}</main>
        <footer className="footer">
          Bank of Abyssinia · Chatbot pilot testing | Internal evaluation platform
        </footer>
      </body>
    </html>
  );
}
