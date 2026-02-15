import { NextResponse } from 'next/server';
import { getMovieById } from '@/lib/movielens';
import { fetchRecommendationsDirect } from '@/lib/api';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const userId = parseInt(searchParams.get('userId') || '1'); // Default to user 1
    const limit = parseInt(searchParams.get('limit') || '10');

    // 1. Get recommended Movie IDs from Python Backend
    const recommendedIds = await fetchRecommendationsDirect(userId, limit);

    // 2. Hydrate with Movie Details (Title, Genres, etc.)
    const movies = await Promise.all(
        recommendedIds.map(async (id) => await getMovieById(id))
    );

    // Filter out any nulls (if ID not found in our CSV)
    const validMovies = movies.filter(m => m !== undefined);

    return NextResponse.json(validMovies);
}
