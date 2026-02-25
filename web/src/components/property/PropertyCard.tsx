'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Heart, Bed, Bath, Maximize, MapPin, ExternalLink } from 'lucide-react';
import { Listing, PREFERRED_SECTORS } from '@/types/listing';
import { cn } from '@/lib/utils';

interface PropertyCardProps {
  listing: Listing;
  onFavorite?: (id: number) => void;
  isFavorite?: boolean;
}

export function PropertyCard({ listing, onFavorite, isFavorite = false }: PropertyCardProps) {
  const images = typeof listing.images === 'string' 
    ? JSON.parse(listing.images || '[]') 
    : listing.images || [];
  
  const mainImage = images[0] || '/placeholder-house.jpg';
  
  const sector = extractSector(listing.location);
  const isPreferred = PREFERRED_SECTORS.some(s => 
    sector.toLowerCase().includes(s.toLowerCase())
  );

  const pricePerSqm = listing.price_usd && listing.sqm 
    ? Math.round(listing.price_usd / listing.sqm) 
    : null;

  const propertyTypeEmoji = {
    casa: '🏠',
    apartamento: '🏢',
    townhouse: '🏘️',
    terreno: '🏗️',
    comercial: '🏪',
  }[listing.property_type || ''] || '🏠';

  return (
    <Card className="group overflow-hidden hover:shadow-lg transition-all duration-300">
      {/* Image Container */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <Image
          src={mainImage}
          alt={listing.text?.slice(0, 50) || 'Propiedad'}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-300"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
        
        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-wrap gap-1">
          {listing.property_type && (
            <Badge variant="secondary" className="bg-background/90 backdrop-blur-sm">
              {propertyTypeEmoji} {listing.property_type}
            </Badge>
          )}
          {isPreferred && (
            <Badge className="bg-yellow-500/90 text-yellow-950 backdrop-blur-sm">
              ⭐ Zona Preferida
            </Badge>
          )}
        </div>

        {/* Favorite Button */}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 bg-background/80 backdrop-blur-sm hover:bg-background"
          onClick={(e) => {
            e.preventDefault();
            onFavorite?.(listing.id);
          }}
        >
          <Heart 
            className={cn(
              "h-5 w-5 transition-colors",
              isFavorite ? "fill-red-500 text-red-500" : "text-muted-foreground"
            )} 
          />
        </Button>

        {/* Price Overlay */}
        {listing.price_usd && (
          <div className="absolute bottom-2 left-2 bg-background/95 backdrop-blur-sm rounded-lg px-3 py-1.5">
            <span className="text-lg font-bold text-primary">
              ${listing.price_usd.toLocaleString()}
            </span>
            {pricePerSqm && (
              <span className="text-xs text-muted-foreground ml-2">
                ${pricePerSqm}/m²
              </span>
            )}
          </div>
        )}
      </div>

      <CardContent className="p-4">
        {/* Location */}
        <div className="flex items-start gap-1 mb-2">
          <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
          <span className="text-sm text-muted-foreground line-clamp-1">
            {sector || listing.location || 'Maracaibo'}
          </span>
        </div>

        {/* Features */}
        <div className="flex items-center gap-4 mb-3">
          {listing.bedrooms && (
            <div className="flex items-center gap-1 text-sm">
              <Bed className="h-4 w-4 text-muted-foreground" />
              <span>{listing.bedrooms}</span>
            </div>
          )}
          {listing.bathrooms && (
            <div className="flex items-center gap-1 text-sm">
              <Bath className="h-4 w-4 text-muted-foreground" />
              <span>{listing.bathrooms}</span>
            </div>
          )}
          {listing.sqm && (
            <div className="flex items-center gap-1 text-sm">
              <Maximize className="h-4 w-4 text-muted-foreground" />
              <span>{listing.sqm}m²</span>
            </div>
          )}
        </div>

        {/* Description Preview */}
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {listing.text?.slice(0, 100) || 'Sin descripción'}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {listing.author || 'Vendedor'}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/propiedad/${listing.id}`}>
                Ver más
              </Link>
            </Button>
            {listing.url && (
              <Button variant="ghost" size="icon" asChild>
                <a href={listing.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function extractSector(location: string | null): string {
  if (!location) return '';
  
  const loc = location.toLowerCase();
  
  // Check for known sectors
  const sectors = [
    'Bella Vista', 'Tierra Negra', 'La Lago', 'Lago Mar Beach', 'Santa Lucia',
    'El Milagro', 'Sabaneta', 'Juana de Avila', 'Virginia', 'La Virginia',
    'Cecilio Acosta', 'Don Bosco', 'La Victoria', 'Las Mercedes', 'Amparo',
    'Coquivacoa', 'Chiquinquira', 'Santa Fe', 'La Limpia', 'Ciudadela',
    'Pomona', 'Indio Mara', 'Monte Claro', 'Monte Bello', 'La Paragua',
    'Los Olivos', 'San Francisco', 'La Coromoto', 'Paraiso', 'Delicias',
    '5 de Julio', 'Padilla', 'Canta Claro', 'Irama', 'El Naranjal',
    'Panamericano', 'Los Haticos', 'Raul Leoni', 'El Trebol', 'Bancomara',
    'Isla Dorada', 'Las Naciones', 'San Jacinto', 'El Rosal', 'Av. 72',
    'La Florida', 'Los Estanques', 'Zona Norte'
  ];
  
  for (const sector of sectors) {
    if (loc.includes(sector.toLowerCase())) {
      return sector;
    }
  }
  
  // Extract from " - " format
  if (location.includes(' - ')) {
    return location.split(' - ').pop()?.trim().slice(0, 30) || '';
  }
  
  return location.slice(0, 30);
}
