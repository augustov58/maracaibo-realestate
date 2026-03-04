'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Bell, Loader2 } from 'lucide-react';
import { createClient } from '@/lib/supabase';

interface CreateAlertDialogProps {
  disabled?: boolean;
}

export function CreateAlertDialog({ disabled }: CreateAlertDialogProps) {
  const searchParams = useSearchParams();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [frequency, setFrequency] = useState('daily');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Build filters object from current search params
  const getFilters = () => {
    const filters: Record<string, string | number> = {};
    
    const q = searchParams.get('q');
    const propertyType = searchParams.get('property_type');
    const sector = searchParams.get('sector');
    const minPrice = searchParams.get('min_price');
    const maxPrice = searchParams.get('max_price');
    const minBedrooms = searchParams.get('min_bedrooms');
    const minSqm = searchParams.get('min_sqm');
    const maxSqm = searchParams.get('max_sqm');

    if (q) filters.q = q;
    if (propertyType) filters.property_type = propertyType;
    if (sector) filters.sector = sector;
    if (minPrice) filters.min_price = parseInt(minPrice);
    if (maxPrice) filters.max_price = parseInt(maxPrice);
    if (minBedrooms) filters.min_bedrooms = parseInt(minBedrooms);
    if (minSqm) filters.min_sqm = parseInt(minSqm);
    if (maxSqm) filters.max_sqm = parseInt(maxSqm);

    return filters;
  };

  // Generate default name from filters
  const generateDefaultName = () => {
    const filters = getFilters();
    const parts: string[] = [];
    
    if (filters.property_type) {
      parts.push(filters.property_type as string);
    }
    if (filters.sector) {
      parts.push(`en ${filters.sector}`);
    }
    if (filters.max_price) {
      parts.push(`hasta $${(filters.max_price as number).toLocaleString()}`);
    }
    if (filters.q) {
      parts.push(`"${filters.q}"`);
    }

    return parts.length > 0 ? parts.join(' ') : 'Mi alerta';
  };

  const handleOpen = (isOpen: boolean) => {
    if (isOpen) {
      setName(generateDefaultName());
      setError('');
      setSuccess(false);
    }
    setOpen(isOpen);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const supabase = createClient();
      
      // Check if user is logged in
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        setError('Debes iniciar sesión para crear alertas');
        setLoading(false);
        return;
      }

      const filters = getFilters();
      
      if (Object.keys(filters).length === 0) {
        setError('Agrega al menos un filtro a tu búsqueda');
        setLoading(false);
        return;
      }

      const { error: insertError } = await supabase
        .from('mcv_alerts')
        .insert({
          user_id: user.id,
          name: name || generateDefaultName(),
          filters,
          frequency,
        });

      if (insertError) {
        console.error('Error creating alert:', insertError);
        setError('Error al crear la alerta. Intenta de nuevo.');
        setLoading(false);
        return;
      }

      setSuccess(true);
      setTimeout(() => {
        setOpen(false);
        setSuccess(false);
      }, 2000);
    } catch (err) {
      console.error('Error:', err);
      setError('Error inesperado. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const hasFilters = Object.keys(getFilters()).length > 0;

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" disabled={disabled || !hasFilters}>
          <Bell className="h-4 w-4 mr-2" />
          Crear alerta
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Crear alerta de búsqueda</DialogTitle>
          <DialogDescription>
            Te notificaremos cuando haya nuevas propiedades que coincidan con tu búsqueda.
          </DialogDescription>
        </DialogHeader>
        
        {success ? (
          <div className="py-8 text-center">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-lg font-medium">¡Alerta creada!</p>
            <p className="text-muted-foreground text-sm">
              Te notificaremos cuando haya nuevas propiedades.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Nombre de la alerta
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="ej: Casas en Bella Vista"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Frecuencia de notificación
                </label>
                <Select value={frequency} onValueChange={setFrequency}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="instant">Inmediato</SelectItem>
                    <SelectItem value="daily">Diario</SelectItem>
                    <SelectItem value="weekly">Semanal</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="bg-muted p-3 rounded-lg">
                <p className="text-sm font-medium mb-2">Filtros guardados:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {Object.entries(getFilters()).map(([key, value]) => (
                    <li key={key}>
                      • {key.replace(/_/g, ' ')}: {String(value)}
                    </li>
                  ))}
                </ul>
              </div>

              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSubmit} disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Crear alerta
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
