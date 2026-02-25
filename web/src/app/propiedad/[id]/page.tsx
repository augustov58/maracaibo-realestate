import { notFound } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft, 
  Heart, 
  Share2, 
  ExternalLink, 
  MapPin, 
  Bed, 
  Bath, 
  Maximize, 
  Calendar,
  User,
  Phone,
  MessageCircle
} from 'lucide-react';
import { Listing, PREFERRED_SECTORS } from '@/types/listing';

async function getListing(id: string): Promise<Listing | null> {
  try {
    const Database = (await import('better-sqlite3')).default;
    const path = await import('path');
    const dbPath = path.join(process.cwd(), '..', 'data', 'listings.db');
    const db = new Database(dbPath, { readonly: true });
    
    const listing = db.prepare('SELECT * FROM listings WHERE id = ?').get(parseInt(id)) as Listing | undefined;
    db.close();
    
    return listing || null;
  } catch (error) {
    console.error('Error fetching listing:', error);
    return null;
  }
}

export default async function PropertyPage({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const { id } = await params;
  const listing = await getListing(id);
  
  if (!listing) {
    notFound();
  }

  const images = typeof listing.images === 'string' 
    ? JSON.parse(listing.images || '[]') 
    : listing.images || [];
  
  const sector = extractSector(listing.location);
  const isPreferred = PREFERRED_SECTORS.some(s => 
    sector.toLowerCase().includes(s.toLowerCase())
  );

  const pricePerSqm = listing.price_usd && listing.sqm 
    ? Math.round(listing.price_usd / listing.sqm) 
    : null;

  const propertyTypeLabel = {
    casa: '🏠 Casa',
    apartamento: '🏢 Apartamento',
    townhouse: '🏘️ Townhouse',
    terreno: '🏗️ Terreno',
    comercial: '🏪 Comercial',
  }[listing.property_type || ''] || '🏠 Propiedad';

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Back Button */}
      <div className="container px-4 py-4">
        <Button variant="ghost" asChild>
          <Link href="/buscar">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver a búsqueda
          </Link>
        </Button>
      </div>

      <div className="container px-4 pb-12">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image Gallery */}
            <Card className="overflow-hidden">
              <div className="relative aspect-[16/10]">
                <Image
                  src={images[0] || '/placeholder-house.jpg'}
                  alt={listing.text?.slice(0, 50) || 'Propiedad'}
                  fill
                  className="object-cover"
                  priority
                />
                {isPreferred && (
                  <Badge className="absolute top-4 left-4 bg-yellow-500 text-yellow-950">
                    ⭐ Zona Preferida
                  </Badge>
                )}
              </div>
              
              {/* Thumbnails */}
              {images.length > 1 && (
                <div className="p-4 flex gap-2 overflow-x-auto">
                  {images.slice(1, 6).map((img: string, i: number) => (
                    <div key={i} className="relative w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden">
                      <Image
                        src={img}
                        alt={`Imagen ${i + 2}`}
                        fill
                        className="object-cover"
                      />
                    </div>
                  ))}
                  {images.length > 6 && (
                    <div className="w-24 h-24 flex-shrink-0 rounded-lg bg-muted flex items-center justify-center">
                      <span className="text-sm text-muted-foreground">+{images.length - 6}</span>
                    </div>
                  )}
                </div>
              )}
            </Card>

            {/* Property Info */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <Badge variant="secondary" className="mb-2">
                      {propertyTypeLabel}
                    </Badge>
                    <CardTitle className="text-2xl">
                      {sector || listing.location || 'Maracaibo'}
                    </CardTitle>
                    <div className="flex items-center text-muted-foreground mt-1">
                      <MapPin className="h-4 w-4 mr-1" />
                      <span>{listing.location || 'Maracaibo, Zulia'}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="icon">
                      <Heart className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon">
                      <Share2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-6">
                {/* Price */}
                {listing.price_usd && (
                  <div className="bg-primary/5 rounded-lg p-4">
                    <div className="text-3xl font-bold text-primary">
                      ${listing.price_usd.toLocaleString()}
                    </div>
                    {pricePerSqm && (
                      <div className="text-muted-foreground">
                        ${pricePerSqm}/m²
                      </div>
                    )}
                  </div>
                )}

                {/* Features */}
                <div className="grid grid-cols-3 gap-4">
                  {listing.bedrooms && (
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <Bed className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="font-semibold">{listing.bedrooms}</div>
                      <div className="text-xs text-muted-foreground">Habitaciones</div>
                    </div>
                  )}
                  {listing.bathrooms && (
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <Bath className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="font-semibold">{listing.bathrooms}</div>
                      <div className="text-xs text-muted-foreground">Baños</div>
                    </div>
                  )}
                  {listing.sqm && (
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <Maximize className="h-6 w-6 mx-auto mb-2 text-primary" />
                      <div className="font-semibold">{listing.sqm}m²</div>
                      <div className="text-xs text-muted-foreground">Superficie</div>
                    </div>
                  )}
                </div>

                <Separator />

                {/* Description */}
                <div>
                  <h3 className="font-semibold mb-3">Descripción</h3>
                  <p className="text-muted-foreground whitespace-pre-wrap">
                    {listing.text || 'Sin descripción disponible.'}
                  </p>
                </div>

                <Separator />

                {/* Details */}
                <div>
                  <h3 className="font-semibold mb-3">Detalles</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Fuente</span>
                      <span className="font-medium capitalize">{listing.source}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Publicado</span>
                      <span className="font-medium">
                        {listing.listing_date || listing.created_at?.split('T')[0]}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">ID</span>
                      <span className="font-medium">#{listing.id}</span>
                    </div>
                    {listing.likes > 0 && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Likes</span>
                        <span className="font-medium">{listing.likes}</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Contact Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Contactar vendedor</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <div className="font-medium">{listing.author || 'Vendedor'}</div>
                    <div className="text-sm text-muted-foreground capitalize">{listing.source}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Button className="w-full" size="lg">
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Enviar mensaje
                  </Button>
                  <Button variant="outline" className="w-full" size="lg">
                    <Phone className="h-4 w-4 mr-2" />
                    Ver teléfono
                  </Button>
                  {listing.url && (
                    <Button variant="ghost" className="w-full" asChild>
                      <a href={listing.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Ver publicación original
                      </a>
                    </Button>
                  )}
                </div>

                <p className="text-xs text-muted-foreground text-center">
                  Al contactar, menciona que viste esta propiedad en Mi Casa Mcbo
                </p>
              </CardContent>
            </Card>

            {/* Alert Card */}
            <Card className="bg-primary/5 border-primary/20">
              <CardContent className="pt-6">
                <div className="text-center">
                  <Calendar className="h-8 w-8 mx-auto mb-2 text-primary" />
                  <h3 className="font-semibold mb-1">¿Te interesa esta zona?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Crea una alerta y te avisamos cuando aparezcan propiedades similares.
                  </p>
                  <Button variant="outline" className="w-full">
                    Crear alerta
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function extractSector(location: string | null): string {
  if (!location) return '';
  
  const loc = location.toLowerCase();
  const sectors = [
    'Bella Vista', 'Tierra Negra', 'La Lago', 'El Milagro', 'Sabaneta',
    'Juana de Avila', 'Virginia', 'Cecilio Acosta', 'Don Bosco', 
    '5 de Julio', 'Canta Claro', 'Bancomara', 'Av. 72', 'Zona Norte',
    'Santa Rita', 'Lago Mar Beach', 'San Francisco', 'Isla Dorada'
  ];
  
  for (const sector of sectors) {
    if (loc.includes(sector.toLowerCase())) {
      return sector;
    }
  }
  
  if (location.includes(' - ')) {
    return location.split(' - ').pop()?.trim().slice(0, 30) || '';
  }
  
  return location.slice(0, 30);
}
