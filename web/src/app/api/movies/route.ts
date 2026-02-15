import { NextResponse } from 'next/server';
import { getMovies } from '@/lib/movielens';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const search = searchParams.get('search') || undefined;

    const data = await getMovies(page, limit, search);
    return NextResponse.json(data);
}
