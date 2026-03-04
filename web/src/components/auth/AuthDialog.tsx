'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Loader2, Mail } from 'lucide-react';
import { createClient } from '@/lib/supabase';

type AuthMode = 'login' | 'register' | 'magic-link';

interface AuthDialogProps {
  trigger?: React.ReactNode;
  defaultOpen?: boolean;
}

export function AuthDialog({ trigger, defaultOpen = false }: AuthDialogProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const resetState = () => {
    setEmail('');
    setPassword('');
    setError('');
    setSuccess('');
    setLoading(false);
  };

  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      resetState();
      setMode('login');
    }
  };

  const handleMagicLink = async () => {
    if (!email) {
      setError('Ingresa tu email');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        setError(error.message);
      } else {
        setSuccess('¡Revisa tu email! Te enviamos un enlace para iniciar sesión.');
      }
    } catch (err) {
      setError('Error inesperado. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailAuth = async () => {
    if (!email || !password) {
      setError('Completa todos los campos');
      return;
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const supabase = createClient();

      if (mode === 'register') {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });

        if (error) {
          setError(error.message);
        } else {
          setSuccess('¡Cuenta creada! Revisa tu email para confirmar.');
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) {
          if (error.message.includes('Invalid login')) {
            setError('Email o contraseña incorrectos');
          } else {
            setError(error.message);
          }
        } else {
          setOpen(false);
          window.location.reload();
        }
      }
    } catch (err) {
      setError('Error inesperado. Intenta de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || <Button variant="ghost">Iniciar Sesión</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'login' && 'Iniciar Sesión'}
            {mode === 'register' && 'Crear Cuenta'}
            {mode === 'magic-link' && 'Enlace Mágico'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'magic-link' 
              ? 'Te enviaremos un enlace a tu email para iniciar sesión sin contraseña.'
              : 'Accede para guardar favoritos y crear alertas de búsqueda.'}
          </DialogDescription>
        </DialogHeader>

        {success ? (
          <div className="py-6 text-center">
            <div className="text-4xl mb-3">📧</div>
            <p className="text-sm text-muted-foreground">{success}</p>
          </div>
        ) : (
          <div className="space-y-4 py-4">
            <div>
              <Input
                type="email"
                placeholder="tu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            {mode !== 'magic-link' && (
              <div>
                <Input
                  type="password"
                  placeholder="Contraseña"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  onKeyDown={(e) => e.key === 'Enter' && handleEmailAuth()}
                />
              </div>
            )}

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            {mode === 'magic-link' ? (
              <Button onClick={handleMagicLink} disabled={loading} className="w-full">
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                <Mail className="h-4 w-4 mr-2" />
                Enviar enlace
              </Button>
            ) : (
              <Button onClick={handleEmailAuth} disabled={loading} className="w-full">
                {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {mode === 'login' ? 'Iniciar Sesión' : 'Crear Cuenta'}
              </Button>
            )}

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">o</span>
              </div>
            </div>

            {mode !== 'magic-link' && (
              <Button 
                variant="outline" 
                onClick={() => setMode('magic-link')}
                className="w-full"
              >
                <Mail className="h-4 w-4 mr-2" />
                Continuar con enlace mágico
              </Button>
            )}

            <div className="text-center text-sm">
              {mode === 'login' && (
                <p className="text-muted-foreground">
                  ¿No tienes cuenta?{' '}
                  <button 
                    onClick={() => { setMode('register'); setError(''); }}
                    className="text-primary hover:underline"
                  >
                    Regístrate
                  </button>
                </p>
              )}
              {mode === 'register' && (
                <p className="text-muted-foreground">
                  ¿Ya tienes cuenta?{' '}
                  <button 
                    onClick={() => { setMode('login'); setError(''); }}
                    className="text-primary hover:underline"
                  >
                    Inicia sesión
                  </button>
                </p>
              )}
              {mode === 'magic-link' && (
                <p className="text-muted-foreground">
                  <button 
                    onClick={() => { setMode('login'); setError(''); }}
                    className="text-primary hover:underline"
                  >
                    Volver al login normal
                  </button>
                </p>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
