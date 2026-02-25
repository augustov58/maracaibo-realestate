import { NextRequest, NextResponse } from 'next/server';
import Database from 'better-sqlite3';
import path from 'path';

// Database path - relative to project root
const DB_PATH = path.join(process.cwd(), '..', 'data', 'listings.db');

interface QueryParams {
  property_type?: string;
  sector?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_sqm?: number;
  max_sqm?: number;
  sort_by?: string;
  page?: number;
  limit?: number;
}

const PREFERRED_SECTORS = [
  'Tierra Negra', 'El Milagro', 'Av. El Milagro', 'Bancomara', 'Banco Mara',
  '5 de Julio', 'Milagro', 'Santa Rita', 'La Lago', 'Bella Vista',
  'Canta Claro', 'Av. 72', 'Zona Norte'
];

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    
    const params: QueryParams = {
      property_type: searchParams.get('property_type') || undefined,
      sector: searchParams.get('sector') || undefined,
      min_price: searchParams.get('min_price') ? parseInt(searchParams.get('min_price')!) : undefined,
      max_price: searchParams.get('max_price') ? parseInt(searchParams.get('max_price')!) : undefined,
      min_bedrooms: searchParams.get('min_bedrooms') ? parseInt(searchParams.get('min_bedrooms')!) : undefined,
      min_sqm: searchParams.get('min_sqm') ? parseInt(searchParams.get('min_sqm')!) : undefined,
      max_sqm: searchParams.get('max_sqm') ? parseInt(searchParams.get('max_sqm')!) : undefined,
      sort_by: searchParams.get('sort_by') || 'date_desc',
      page: searchParams.get('page') ? parseInt(searchParams.get('page')!) : 1,
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 20,
    };

    const db = new Database(DB_PATH, { readonly: true });
    
    // Build query
    let whereClause = 'WHERE 1=1';
    const queryParams: (string | number)[] = [];
    
    // Exclude rentals (price < 1000)
    whereClause += ' AND (price_usd IS NULL OR price_usd >= 1000)';
    
    if (params.property_type) {
      whereClause += ' AND property_type = ?';
      queryParams.push(params.property_type);
    }
    
    if (params.sector === 'preferred') {
      // Filter by preferred sectors
      const sectorConditions = PREFERRED_SECTORS.map(() => 'location LIKE ?').join(' OR ');
      whereClause += ` AND (${sectorConditions})`;
      PREFERRED_SECTORS.forEach(s => queryParams.push(`%${s}%`));
    } else if (params.sector) {
      whereClause += ' AND location LIKE ?';
      queryParams.push(`%${params.sector}%`);
    }
    
    if (params.min_price) {
      whereClause += ' AND price_usd >= ?';
      queryParams.push(params.min_price);
    }
    
    if (params.max_price) {
      whereClause += ' AND price_usd <= ?';
      queryParams.push(params.max_price);
    }
    
    if (params.min_bedrooms) {
      whereClause += ' AND bedrooms >= ?';
      queryParams.push(params.min_bedrooms);
    }
    
    if (params.min_sqm) {
      whereClause += ' AND sqm >= ?';
      queryParams.push(params.min_sqm);
    }
    
    if (params.max_sqm) {
      whereClause += ' AND sqm <= ?';
      queryParams.push(params.max_sqm);
    }
    
    // Sort
    let orderBy = 'ORDER BY created_at DESC';
    switch (params.sort_by) {
      case 'price_asc':
        orderBy = 'ORDER BY price_usd ASC NULLS LAST';
        break;
      case 'price_desc':
        orderBy = 'ORDER BY price_usd DESC NULLS LAST';
        break;
      case 'sqm_desc':
        orderBy = 'ORDER BY sqm DESC NULLS LAST';
        break;
      case 'date_desc':
      default:
        orderBy = 'ORDER BY created_at DESC';
    }
    
    // Count total
    const countQuery = `SELECT COUNT(*) as total FROM listings ${whereClause}`;
    const countResult = db.prepare(countQuery).get(...queryParams) as { total: number };
    
    // Get listings
    const offset = ((params.page || 1) - 1) * (params.limit || 20);
    const listingsQuery = `
      SELECT * FROM listings 
      ${whereClause} 
      ${orderBy}
      LIMIT ? OFFSET ?
    `;
    
    const listings = db.prepare(listingsQuery).all(...queryParams, params.limit || 20, offset);
    
    db.close();
    
    return NextResponse.json({
      listings,
      total: countResult.total,
      page: params.page || 1,
      limit: params.limit || 20,
      totalPages: Math.ceil(countResult.total / (params.limit || 20)),
    });
  } catch (error) {
    console.error('Error fetching listings:', error);
    return NextResponse.json(
      { error: 'Failed to fetch listings' },
      { status: 500 }
    );
  }
}
