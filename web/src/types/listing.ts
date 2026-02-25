export interface Listing {
  id: number;
  source: string;
  source_id: string;
  url: string;
  text: string;
  author: string;
  timestamp: string;
  images: string[];
  likes: number;
  price_usd: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  sqm: number | null;
  property_type: string | null;
  location: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  listing_date: string | null;
}

export interface ListingFilters {
  property_type?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_sqm?: number;
  max_sqm?: number;
  sector?: string;
  sort_by?: 'price_asc' | 'price_desc' | 'date_desc' | 'sqm_desc' | 'opportunity';
}

export interface SearchResult {
  listings: Listing[];
  total: number;
  page: number;
  limit: number;
}

export const PROPERTY_TYPES = [
  { value: 'casa', label: 'Casa' },
  { value: 'apartamento', label: 'Apartamento' },
  { value: 'townhouse', label: 'Townhouse' },
  { value: 'terreno', label: 'Terreno' },
  { value: 'comercial', label: 'Comercial' },
] as const;

export const PREFERRED_SECTORS = [
  'Tierra Negra',
  'El Milagro', 
  'Av. El Milagro',
  'Bancomara',
  'Banco Mara',
  '5 de Julio',
  'Milagro',
  'Santa Rita',
  'La Lago',
  'Bella Vista',
  'Canta Claro',
  'Av. 72',
  'Zona Norte',
] as const;

export const ALL_SECTORS = [
  ...PREFERRED_SECTORS,
  'Sabaneta',
  'Juana de Avila',
  'Virginia',
  'La Virginia',
  'Cecilio Acosta',
  'Don Bosco',
  'La Victoria',
  'Las Mercedes',
  'Amparo',
  'Coquivacoa',
  'Chiquinquira',
  'Santa Fe',
  'La Limpia',
  'Ciudadela',
  'Pomona',
  'Indio Mara',
  'Monte Claro',
  'Monte Bello',
  'La Paragua',
  'Los Olivos',
  'San Francisco',
  'La Coromoto',
  'Paraiso',
  'Delicias',
  'Padilla',
  'Irama',
  'El Naranjal',
  'Panamericano',
  'Los Haticos',
  'Raul Leoni',
  'El Trebol',
  'Isla Dorada',
  'Las Naciones',
  'San Jacinto',
  'El Rosal',
  'La Florida',
  'Los Estanques',
  'Santa Lucia',
  'Lago Mar Beach',
] as const;
