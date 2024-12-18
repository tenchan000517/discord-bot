import './globals.css'
import { Providers } from './providers'

export const metadata = {
  title: 'Discord Server Dashboard',
  description: 'Dashboard for Discord Gacha Bot',
}

export default function RootLayout({ children }) {
  return (
    <html lang="ja">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}