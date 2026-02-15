import { NextResponse } from 'next/server';
import { getRecommendations } from '@/lib/movielens';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const userId = parseInt(searchParams.get('userId') || '1'); // Default to user 1
    const limit = parseInt(searchParams.get('limit') || '10');

    const movies = await getRecommendations(userId, limit);
    return NextResponse.json(movies);
}
