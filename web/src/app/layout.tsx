import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header } from '@/components/layout/Header';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Mi Casa Venezuela | Encuentra tu hogar ideal',
  description: 'El mejor buscador de propiedades en Venezuela. Casas, apartamentos, townhouses y más en las mejores zonas de Maracaibo y todo el país.',
  keywords: 'inmuebles venezuela, casas maracaibo, apartamentos venezuela, bienes raices venezuela, propiedades zulia',
  openGraph: {
    title: 'Mi Casa Venezuela | Encuentra tu hogar ideal',
    description: 'El mejor buscador de propiedades en Venezuela.',
    type: 'website',
    locale: 'es_VE',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1">
            {children}
          </main>
          <footer className="border-t py-8 mt-auto">
            <div className="container px-4 text-center text-sm text-muted-foreground">
              <p>© {new Date().getFullYear()} Mi Casa Venezuela. Todos los derechos reservados.</p>
              <p className="mt-1">
                Maracaibo, Venezuela 🇻🇪
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
