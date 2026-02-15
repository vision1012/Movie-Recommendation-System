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

    const similar = await getSimilarMovies(movieId);

    return NextResponse.json({ ...movie, similar });
}
