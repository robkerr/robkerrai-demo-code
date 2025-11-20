import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Image Repository',
  description: 'Upload and search images using vector similarity',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

