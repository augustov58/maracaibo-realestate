import { Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { SearchFilters } from '@/components/search/SearchFilters';
import { PropertyCard } from '@/components/property/PropertyCard';
import { Building2, TrendingUp, Users, Shield, ArrowRight, MapPin } from 'lucide-react';
import { Listing } from '@/types/listing';

async function getFeaturedListings(): Promise<Listing[]> {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
    const res = await fetch(`${baseUrl}/api/listings?limit=6&sector=preferred`, {
      next: { revalidate: 300 } // Cache for 5 minutes
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.listings || [];
  } catch {
    return [];
  }
}

async function getStats() {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
    const res = await fetch(`${baseUrl}/api/listings?limit=1`, {
      next: { revalidate: 300 }
    });
    if (!res.ok) return { total: 0 };
    const data = await res.json();
    return { total: data.total || 0 };
  } catch {
    return { total: 0 };
  }
}

export default async function HomePage() {
  const [featuredListings, stats] = await Promise.all([
    getFeaturedListings(),
    getStats()
  ]);

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 bg-gradient-to-br from-primary/10 via-background to-background">
        <div className="container px-4">
          <div className="max-w-3xl mx-auto text-center mb-10">
            <Badge variant="secondary" className="mb-4">
              🏠 +{stats.total} propiedades disponibles
            </Badge>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Encuentra tu hogar ideal en{' '}
              <span className="text-primary">Maracaibo</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8">
              El mejor buscador de propiedades en la ciudad. Casas, apartamentos y más 
              en las mejores zonas del Zulia.
            </p>
          </div>
          
          {/* Search Bar */}
          <Suspense fallback={<Skeleton className="h-16 max-w-4xl mx-auto rounded-xl" />}>
            <SearchFilters compact />
          </Suspense>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-b">
        <div className="container px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <StatCard 
              icon={Building2} 
              value={stats.total.toString()} 
              label="Propiedades" 
            />
            <StatCard 
              icon={MapPin} 
              value="40+" 
              label="Sectores" 
            />
            <StatCard 
              icon={Users} 
              value="10+" 
              label="Realtors" 
            />
            <StatCard 
              icon={TrendingUp} 
              value="24h" 
              label="Actualización" 
            />
          </div>
        </div>
      </section>

      {/* Featured Listings */}
      <section className="py-16">
        <div className="container px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold">
                ⭐ Zonas Preferidas
              </h2>
              <p className="text-muted-foreground mt-1">
                Las mejores propiedades en los sectores más buscados
              </p>
            </div>
            <Button variant="outline" asChild>
              <Link href="/buscar?sector=preferred">
                Ver todas
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>

          {featuredListings.length > 0 ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredListings.map((listing) => (
                <PropertyCard key={listing.id} listing={listing} />
              ))}
            </div>
          ) : (
            <Card className="p-12 text-center">
              <CardContent>
                <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Cargando propiedades...</h3>
                <p className="text-muted-foreground">
                  Las propiedades aparecerán aquí pronto.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-muted/50">
        <div className="container px-4">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              ¿Por qué Mi Casa Mcbo?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Reunimos las mejores propiedades de múltiples fuentes para ahorrarte tiempo
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={Building2}
              title="Múltiples Fuentes"
              description="Agregamos listings de Instagram, websites de realtors y más en un solo lugar."
            />
            <FeatureCard
              icon={TrendingUp}
              title="Datos Actualizados"
              description="Información actualizada varias veces al día con precios y disponibilidad real."
            />
            <FeatureCard
              icon={Shield}
              title="Filtros Inteligentes"
              description="Encuentra exactamente lo que buscas con filtros avanzados por zona, precio y más."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16">
        <div className="container px-4">
          <Card className="bg-primary text-primary-foreground p-8 md:p-12">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-2xl md:text-3xl font-bold mb-4">
                ¿Buscando algo específico?
              </h2>
              <p className="text-primary-foreground/80 mb-6">
                Crea una alerta y te notificamos cuando aparezcan propiedades 
                que coincidan con tus criterios.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button size="lg" variant="secondary" asChild>
                  <Link href="/buscar">
                    Explorar propiedades
                  </Link>
                </Button>
                <Button size="lg" variant="outline" className="border-primary-foreground/20 hover:bg-primary-foreground/10">
                  Crear alerta
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

function StatCard({ icon: Icon, value, label }: { icon: React.ElementType; value: string; label: string }) {
  return (
    <div className="text-center">
      <Icon className="h-8 w-8 mx-auto text-primary mb-2" />
      <div className="text-2xl md:text-3xl font-bold">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <Card className="p-6 text-center hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <h3 className="font-semibold text-lg mb-2">{title}</h3>
        <p className="text-muted-foreground text-sm">{description}</p>
      </CardContent>
    </Card>
  );
}
