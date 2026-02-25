import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.cdninstagram.com',
      },
      {
        protocol: 'https',
        hostname: 'scontent.cdninstagram.com',
      },
      {
        protocol: 'https',
        hostname: '**.fbcdn.net',
      },
      {
        protocol: 'https',
        hostname: 'instagram.*.fbcdn.net',
      },
      {
        protocol: 'https',
        hostname: '*.regaladogroup.net',
      },
      {
        protocol: 'https',
        hostname: 'regaladogroup.net',
      },
      {
        protocol: 'https',
        hostname: '*.angelpinton.com',
      },
      {
        protocol: 'https',
        hostname: 'angelpinton.com',
      },
      {
        protocol: 'https',
        hostname: '*.nexthouseinmobiliaria.com',
      },
      {
        protocol: 'https',
        hostname: '*.zuhausebienesraices.com',
      },
      {
        protocol: 'https',
        hostname: '*.eliterealestateca.com',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      },
    ],
    unoptimized: true, // For initial development
  },
  // Enable standalone output for easier deployment
  output: 'standalone',
};

export default nextConfig;
