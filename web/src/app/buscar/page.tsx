'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { PropertyCard } from '@/components/property/PropertyCard';
import { SearchFilters } from '@/components/search/SearchFilters';
import { CreateAlertDialog } from '@/components/search/CreateAlertDialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Listing } from '@/types/listing';
import { Grid3X3, List, ChevronLeft, ChevronRight } from 'lucide-react';

function SearchContent() {
  const searchParams = useSearchParams();
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState('date_desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    async function fetchListings() {
      setLoading(true);
      try {
        const params = new URLSearchParams(searchParams.toString());
        params.set('page', page.toString());
        params.set('sort_by', sortBy);
        params.set('limit', '12');
        
        const res = await fetch(`/api/listings?${params.toString()}`);
        const data = await res.json();
        
        setListings(data.listings || []);
        setTotal(data.total || 0);
        setTotalPages(data.totalPages || 1);
      } catch (error) {
        console.error('Error fetching listings:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchListings();
  }, [searchParams, page, sortBy]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [searchParams]);

  return (
    <div className="container px-4 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Filters Sidebar */}
        <aside className="lg:w-72 flex-shrink-0">
          <SearchFilters />
        </aside>

        {/* Results */}
        <div className="flex-1">
          {/* Results Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold">Propiedades en Maracaibo</h1>
              <p className="text-muted-foreground">
                {loading ? 'Buscando...' : `${total} propiedades encontradas`}
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Create Alert */}
              <CreateAlertDialog />
              
              {/* View Toggle */}
              <div className="flex border rounded-md">
                <Button 
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'} 
                  size="icon"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button 
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'} 
                  size="icon"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
              
              {/* Sort */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Ordenar por" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date_desc">Más recientes</SelectItem>
                  <SelectItem value="price_asc">Menor precio</SelectItem>
                  <SelectItem value="price_desc">Mayor precio</SelectItem>
                  <SelectItem value="sqm_desc">Mayor tamaño</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className={`grid gap-6 ${viewMode === 'grid' ? 'sm:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'}`}>
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-[350px] rounded-xl" />
              ))}
            </div>
          )}

          {/* Results Grid */}
          {!loading && listings.length > 0 && (
            <div className={`grid gap-6 ${viewMode === 'grid' ? 'sm:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'}`}>
              {listings.map((listing) => (
                <PropertyCard key={listing.id} listing={listing} />
              ))}
            </div>
          )}

          {/* No Results */}
          {!loading && listings.length === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🏠</div>
              <h2 className="text-xl font-semibold mb-2">No encontramos propiedades</h2>
              <p className="text-muted-foreground mb-4">
                Intenta ajustar los filtros de búsqueda
              </p>
              <Button variant="outline" onClick={() => window.location.href = '/buscar'}>
                Limpiar filtros
              </Button>
            </div>
          )}

          {/* Pagination */}
          {!loading && totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <Button
                variant="outline"
                size="icon"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              
              <div className="flex items-center gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      variant={page === pageNum ? 'default' : 'outline'}
                      size="icon"
                      onClick={() => setPage(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}
              </div>
              
              <Button
                variant="outline"
                size="icon"
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function BuscarPage() {
  return (
    <Suspense fallback={
      <div className="container px-4 py-8">
        <Skeleton className="h-[600px] w-full" />
      </div>
    }>
      <SearchContent />
    </Suspense>
  );
}
