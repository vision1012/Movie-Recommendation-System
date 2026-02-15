import { NextResponse } from 'next/server';
import { getTrendingMovies } from '@/lib/movielens';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '10');
    const movies = await getTrendingMovies(limit);
    return NextResponse.json(movies);
}
