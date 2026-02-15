import { NextResponse } from 'next/server';
import { getMovieById, getSimilarMovies } from '@/lib/movielens';

export async function GET(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    const { id } = await params;
    const movieId = parseInt(id);
    const movie = await getMovieById(movieId);

    if (!movie) {
        return NextResponse.json({ error: 'Movie not found' }, { status: 404 });
    }

    // Get similar movie IDs from Python Backend
    // Using fetchSimilarMovies which uses localhost direct URL for server-side
    // We need to import it first
    const { fetchSimilarMovies } = await import('@/lib/api');
    const similarIds = await fetchSimilarMovies(movieId);

    // Hydrate similar movies
    const similar = await Promise.all(
        similarIds.map(async (id) => await getMovieById(id))
    );
    const validSimilar = similar.filter(m => m !== undefined);

    return NextResponse.json({ ...movie, similar: validSimilar });
}
