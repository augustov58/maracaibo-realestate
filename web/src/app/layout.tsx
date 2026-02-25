import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header } from '@/components/layout/Header';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Mi Casa Mcbo | Encuentra tu hogar en Maracaibo',
  description: 'El mejor buscador de propiedades en Maracaibo, Venezuela. Casas, apartamentos, townhouses y más en las mejores zonas.',
  keywords: 'inmuebles maracaibo, casas maracaibo, apartamentos maracaibo, bienes raices venezuela, propiedades zulia',
  openGraph: {
    title: 'Mi Casa Mcbo | Encuentra tu hogar en Maracaibo',
    description: 'El mejor buscador de propiedades en Maracaibo, Venezuela.',
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
              <p>© {new Date().getFullYear()} Mi Casa Mcbo. Todos los derechos reservados.</p>
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
