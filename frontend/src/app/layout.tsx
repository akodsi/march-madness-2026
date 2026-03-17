import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '2026 March Madness Predictor',
  description: 'Pick your bracket with confidence-interval predictions',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
