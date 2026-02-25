'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { PROPERTY_TYPES, ALL_SECTORS } from '@/types/listing';

interface SearchFiltersProps {
  compact?: boolean;
}

export function SearchFilters({ compact = false }: SearchFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [filters, setFilters] = useState({
    property_type: searchParams.get('property_type') || '',
    sector: searchParams.get('sector') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    min_bedrooms: searchParams.get('min_bedrooms') || '',
    min_sqm: searchParams.get('min_sqm') || '',
    max_sqm: searchParams.get('max_sqm') || '',
  });

  const [priceRange, setPriceRange] = useState([
    parseInt(filters.min_price) || 0,
    parseInt(filters.max_price) || 500000
  ]);

  const applyFilters = () => {
    const params = new URLSearchParams();
    
    if (filters.property_type) params.set('property_type', filters.property_type);
    if (filters.sector) params.set('sector', filters.sector);
    if (priceRange[0] > 0) params.set('min_price', priceRange[0].toString());
    if (priceRange[1] < 500000) params.set('max_price', priceRange[1].toString());
    if (filters.min_bedrooms) params.set('min_bedrooms', filters.min_bedrooms);
    if (filters.min_sqm) params.set('min_sqm', filters.min_sqm);
    if (filters.max_sqm) params.set('max_sqm', filters.max_sqm);
    
    router.push(`/buscar?${params.toString()}`);
  };

  const clearFilters = () => {
    setFilters({
      property_type: '',
      sector: '',
      min_price: '',
      max_price: '',
      min_bedrooms: '',
      min_sqm: '',
      max_sqm: '',
    });
    setPriceRange([0, 500000]);
    router.push('/buscar');
  };

  const activeFiltersCount = Object.values(filters).filter(v => v).length + 
    (priceRange[0] > 0 || priceRange[1] < 500000 ? 1 : 0);

  // Compact version for homepage
  if (compact) {
    return (
      <div className="flex flex-col sm:flex-row gap-3 p-4 bg-background rounded-xl shadow-lg border max-w-4xl mx-auto">
        <Select
          value={filters.property_type}
          onValueChange={(v) => setFilters(prev => ({ ...prev, property_type: v }))}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Tipo de propiedad" />
          </SelectTrigger>
          <SelectContent>
            {PROPERTY_TYPES.map(type => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.sector}
          onValueChange={(v) => setFilters(prev => ({ ...prev, sector: v }))}
        >
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Sector" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="preferred">⭐ Zonas Preferidas</SelectItem>
            {[...new Set(ALL_SECTORS)].sort().map(sector => (
              <SelectItem key={sector} value={sector}>
                {sector}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="number"
          placeholder="Precio máx."
          className="w-full sm:w-[140px]"
          value={filters.max_price}
          onChange={(e) => setFilters(prev => ({ ...prev, max_price: e.target.value }))}
        />

        <Button onClick={applyFilters} className="w-full sm:w-auto">
          <Search className="h-4 w-4 mr-2" />
          Buscar
        </Button>
      </div>
    );
  }

  // Full filters for search page
  return (
    <div className="space-y-4">
      {/* Mobile Filter Button */}
      <div className="lg:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="outline" className="w-full justify-between">
              <span className="flex items-center">
                <SlidersHorizontal className="h-4 w-4 mr-2" />
                Filtros
              </span>
              {activeFiltersCount > 0 && (
                <span className="bg-primary text-primary-foreground rounded-full px-2 py-0.5 text-xs">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
          </SheetTrigger>
          <SheetContent side="bottom" className="h-[80vh]">
            <SheetHeader>
              <SheetTitle>Filtros de búsqueda</SheetTitle>
            </SheetHeader>
            <div className="mt-4 space-y-6 overflow-y-auto">
              <FilterContent 
                filters={filters} 
                setFilters={setFilters}
                priceRange={priceRange}
                setPriceRange={setPriceRange}
              />
              <div className="flex gap-2 pt-4 border-t">
                <Button variant="outline" onClick={clearFilters} className="flex-1">
                  Limpiar
                </Button>
                <Button onClick={applyFilters} className="flex-1">
                  Aplicar filtros
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop Filters */}
      <div className="hidden lg:block p-6 bg-card rounded-xl border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Filtros</h3>
          {activeFiltersCount > 0 && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Limpiar ({activeFiltersCount})
            </Button>
          )}
        </div>
        <FilterContent 
          filters={filters} 
          setFilters={setFilters}
          priceRange={priceRange}
          setPriceRange={setPriceRange}
        />
        <Button onClick={applyFilters} className="w-full mt-6">
          <Search className="h-4 w-4 mr-2" />
          Buscar
        </Button>
      </div>
    </div>
  );
}

type FiltersState = {
  property_type: string;
  sector: string;
  min_price: string;
  max_price: string;
  min_bedrooms: string;
  min_sqm: string;
  max_sqm: string;
};

interface FilterContentProps {
  filters: FiltersState;
  setFilters: React.Dispatch<React.SetStateAction<FiltersState>>;
  priceRange: number[];
  setPriceRange: React.Dispatch<React.SetStateAction<number[]>>;
}

function FilterContent({ filters, setFilters, priceRange, setPriceRange }: FilterContentProps) {
  return (
    <div className="space-y-6">
      {/* Property Type */}
      <div>
        <label className="text-sm font-medium mb-2 block">Tipo de propiedad</label>
        <Select
          value={filters.property_type}
          onValueChange={(v) => setFilters(prev => ({ ...prev, property_type: v }))}
        >
          <SelectTrigger>
            <SelectValue placeholder="Todos los tipos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            {PROPERTY_TYPES.map(type => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Sector */}
      <div>
        <label className="text-sm font-medium mb-2 block">Sector</label>
        <Select
          value={filters.sector}
          onValueChange={(v) => setFilters(prev => ({ ...prev, sector: v }))}
        >
          <SelectTrigger>
            <SelectValue placeholder="Todos los sectores" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="preferred">⭐ Zonas Preferidas</SelectItem>
            {[...new Set(ALL_SECTORS)].sort().map(sector => (
              <SelectItem key={sector} value={sector}>
                {sector}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Price Range */}
      <div>
        <label className="text-sm font-medium mb-2 block">
          Precio: ${priceRange[0].toLocaleString()} - ${priceRange[1].toLocaleString()}
        </label>
        <Slider
          value={priceRange}
          onValueChange={setPriceRange}
          min={0}
          max={500000}
          step={5000}
          className="mt-2"
        />
      </div>

      {/* Bedrooms */}
      <div>
        <label className="text-sm font-medium mb-2 block">Habitaciones mínimas</label>
        <Select
          value={filters.min_bedrooms}
          onValueChange={(v) => setFilters(prev => ({ ...prev, min_bedrooms: v }))}
        >
          <SelectTrigger>
            <SelectValue placeholder="Cualquiera" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Cualquiera</SelectItem>
            <SelectItem value="1">1+</SelectItem>
            <SelectItem value="2">2+</SelectItem>
            <SelectItem value="3">3+</SelectItem>
            <SelectItem value="4">4+</SelectItem>
            <SelectItem value="5">5+</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Size */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium mb-2 block">m² mín.</label>
          <Input
            type="number"
            placeholder="0"
            value={filters.min_sqm}
            onChange={(e) => setFilters(prev => ({ ...prev, min_sqm: e.target.value }))}
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-2 block">m² máx.</label>
          <Input
            type="number"
            placeholder="∞"
            value={filters.max_sqm}
            onChange={(e) => setFilters(prev => ({ ...prev, max_sqm: e.target.value }))}
          />
        </div>
      </div>
    </div>
  );
}
