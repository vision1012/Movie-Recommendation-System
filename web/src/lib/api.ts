
export interface BackendRecommendation {
    user_id: string;
    recommendations: number[]; // List of movie IDs
}

export interface BackendSimilar {
    item_id: string;
    similar_items: number[];
}

const BACKEND_URL = '/api/python';

export async function fetchRecommendations(userId: number, limit: number = 10): Promise<number[]> {
    try {
        const res = await fetch(`${BACKEND_URL}/recommend?user_id=${userId}&k=${limit}`, {
            // Check if we are checking from server side or client side
            // If server side, we might need absolute URL, but since we set up rewrite, 
            // valid relative URL should work if called from Client Components or via Next.js internal fetch ??
            // Actually, for Server Components, we should direct to localhost:8000 directly to avoid self-request overhead if possible
            // But relying on next.config.ts rewrite is cleaner for client.
            // Let's assume this is primarily called from Next.js API routes (Server environment).
        });

        // If we are running on server, we should probably hit the python API directly if the rewrite doesn't work for server-server communication
        // However, let's try using the rewrite path first. If this fails in the API route, we can switch to direct URL.

        if (!res.ok) {
            console.error('Backend recommendation failed', await res.text());
            return [];
        }

        const data: BackendRecommendation = await res.json();
        return data.recommendations;
    } catch (e) {
        console.error("Error/fallback fetching recommendations:", e);
        return [];
    }
}

export async function fetchSimilarMovies(movieId: number, limit: number = 6): Promise<number[]> {
    try {
        // If running server-side (in Next.js API route), we can't easily use the relative path '/api/python'
        // effectively without a base URL.
        // It's safer to use the direct localhost URL for server-to-server communication
        const url = `http://127.0.0.1:8000/similar?item_id=${movieId}&k=${limit}`;

        const res = await fetch(url);
        if (!res.ok) return [];

        const data: BackendSimilar = await res.json();
        return data.similar_items;
    } catch (e) {
        console.error("Error fetching similar movies:", e);
        return [];
    }
}

// For consistency, let's update fetchRecommendations to use direct URL as well since use case is mostly server-side API route.
export async function fetchRecommendationsDirect(userId: number, limit: number = 10): Promise<number[]> {
    try {
        const url = `http://127.0.0.1:8000/recommend?user_id=${userId}&k=${limit}`;
        const res = await fetch(url);
        if (!res.ok) return [];
        const data: BackendRecommendation = await res.json();
        return data.recommendations;
    } catch (e) {
        console.error("Error fetching recommendations direct:", e);
        return [];
    }
}
