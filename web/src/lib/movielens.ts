import path from 'path';
import fs from 'fs';
import Papa from 'papaparse';

const DATA_DIR = path.join(process.cwd(), '../MovieLens Data');

export interface Movie {
    movieId: number;
    title: string;
    genres: string[];
    year?: number;
    posterUrl?: string; // We'll mock this or fetch from TMDB if possible later
    rating?: number;
    voteCount?: number;
}

export interface Rating {
    userId: number;
    movieId: number;
    rating: number;
    timestamp: number;
}

// Raw types from CSV
interface RawMovie {
    movieId: number;
    title: string;
    genres: string; // Pipe-separated
}

interface RawRating {
    userId: number;
    movieId: number;
    rating: number;
    timestamp: number;
}

interface RawLink {
    movieId: number;
    imdbId: number;
    tmdbId: number;
}

// In-memory cache
let cachedMovies: Movie[] | null = null;

async function loadData() {
    if (cachedMovies) return { movies: cachedMovies };

    try {
        const movieContent = fs.readFileSync(path.join(DATA_DIR, 'movie.csv'), 'utf8');
        const linkContent = fs.readFileSync(path.join(DATA_DIR, 'link.csv'), 'utf8');

        const moviesData = Papa.parse<RawMovie>(movieContent, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;
        const linksData = Papa.parse<RawLink>(linkContent, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;

        // Create a map of movie stats
        const movieStats = new Map<number, { sum: number; count: number }>();

        // Stream ratings.csv instead of reading all at once
        await new Promise<void>((resolve, reject) => {
            const fileStream = fs.createReadStream(path.join(DATA_DIR, 'rating.csv'));
            let count = 0;
            const limit = 500000; // Limit to 500k ratings for performance

            Papa.parse<RawRating>(fileStream, {
                header: true,
                dynamicTyping: true,
                skipEmptyLines: true,
                step: (results, parser) => {
                    const r = results.data;
                    const current = movieStats.get(r.movieId) || { sum: 0, count: 0 };
                    movieStats.set(r.movieId, { sum: current.sum + r.rating, count: current.count + 1 });

                    count++;
                    if (count >= limit) {
                        parser.abort();
                        resolve();
                    }
                },
                complete: () => {
                    resolve();
                },
                error: (err: Error) => {
                    reject(err);
                }
            });
        });

        const linksMap = new Map<number, RawLink>();
        linksData.forEach(l => linksMap.set(l.movieId, l));

        cachedMovies = moviesData.map((m) => {
            const stats = movieStats.get(m.movieId) || { sum: 0, count: 0 };
            const rating = stats.count > 0 ? stats.sum / stats.count : 0;

            // Extract year from title "Toy Story (1995)"
            const yearMatch = m.title.match(/\((\d{4})\)$/);
            const year = yearMatch ? parseInt(yearMatch[1]) : undefined;
            const title = m.title.replace(/\s\(\d{4}\)$/, '');

            const link = linksMap.get(m.movieId);

            return {
                movieId: m.movieId,
                title,
                genres: m.genres.split('|'),
                year,
                rating,
                voteCount: stats.count,
                posterUrl: link?.tmdbId ? `https://image.tmdb.org/t/p/w500/${link.tmdbId}.jpg` : undefined // This won't work without fetch, but good for placeholder structure
            };
        });

        return { movies: cachedMovies };
    } catch (error) {
        console.error("Failed to load MovieLens data:", error);
        return { movies: [] };
    }
}

export async function getMovies(page = 1, limit = 20, search?: string, genre?: string) {
    const { movies } = await loadData();
    let filtered = movies;

    if (search) {
        const query = search.toLowerCase();
        filtered = filtered.filter(m => m.title.toLowerCase().includes(query));
    }

    if (genre && genre !== 'All') {
        filtered = filtered.filter(m => m.genres.includes(genre));
    }

    const start = (page - 1) * limit;
    const end = start + limit;
    return {
        data: filtered.slice(start, end),
        total: filtered.length,
        page,
        limit
    };
}

export async function getMovieById(id: number) {
    const { movies } = await loadData();
    return movies.find(m => m.movieId === id);
}

export async function getTrendingMovies(limit = 10) {
    const { movies } = await loadData();
    // Simple "trending": high rating + significant vote count
    // In a real app, use recent timestamps
    return movies
        .filter(m => (m.voteCount || 0) > 50)
        .sort((a, b) => (b.rating || 0) - (a.rating || 0))
        .slice(0, limit);
}

export async function getRecommendations(userId: number, limit = 10) {
    // For now, return top rated movies as a fallback
    // In next steps, implement actual personalized logic if time permits
    return getTrendingMovies(limit);
}

export async function getGenres() {
    const { movies } = await loadData();
    const genres = new Set<string>();
    movies.forEach(m => m.genres.forEach(g => genres.add(g)));
    return Array.from(genres).sort();
}


export async function getSimilarMovies(movieId: number, limit = 6) {
    const { movies } = await loadData();
    const source = movies.find(m => m.movieId === movieId);
    if (!source) return [];

    // Simple content-based filtering on genres
    return movies
        .filter(m => m.movieId !== movieId && m.genres.some(g => source.genres.includes(g)))
        .sort((a, b) => {
            const aCommon = a.genres.filter(g => source.genres.includes(g)).length;
            const bCommon = b.genres.filter(g => source.genres.includes(g)).length;
            return bCommon - aCommon || (b.rating || 0) - (a.rating || 0);
        })
        .slice(0, limit);
}
