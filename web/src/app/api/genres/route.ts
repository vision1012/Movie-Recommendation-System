import { NextResponse } from 'next/server';
import { getGenres } from '@/lib/movielens';

export async function GET() {
    const genres = await getGenres();
    return NextResponse.json(genres);
}
