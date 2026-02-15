import { getMovies, getGenres } from "@/lib/movielens";
import { MovieCard } from "@/components/movie-card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

interface BrowseProps {
    searchParams: Promise<{
        genre?: string;
        page?: string;
    }>;
}

export default async function BrowsePage({ searchParams }: BrowseProps) {
    const { genre, page } = await searchParams;
    const currentPage = parseInt(page || '1');
    const selectedGenre = genre || 'All';

    const { data: movies, total, limit } = await getMovies(currentPage, 30, undefined, selectedGenre);
    const genres = await getGenres();

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <h1 className="text-3xl font-serif font-bold text-white">Browse Movies</h1>

                {/* Genre Filter Pills */}
                <div className="flex flex-wrap gap-2">
                    <Link href="/browse">
                        <Button
                            variant={selectedGenre === 'All' ? 'default' : 'outline'}
                            size="sm"
                            className={`rounded-full ${selectedGenre === 'All' ? 'bg-gold-500 text-midnight-950 hover:bg-gold-400' : 'bg-transparent border-white/20 text-slate-300 hover:text-white'}`}
                        >
                            All
                        </Button>
                    </Link>
                    {genres.map(g => (
                        <Link key={g} href={`/browse?genre=${g}`}>
                            <Button
                                variant={selectedGenre === g ? 'default' : 'outline'}
                                size="sm"
                                className={`rounded-full ${selectedGenre === g ? 'bg-gold-500 text-midnight-950 hover:bg-gold-400' : 'bg-transparent border-white/20 text-slate-300 hover:text-white'}`}
                            >
                                {g}
                            </Button>
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
                {movies.length > 0 ? (
                    movies.map((movie) => (
                        <div key={movie.movieId} className="flex justify-center">
                            <MovieCard movie={movie} />
                        </div>
                    ))
                ) : (
                    <div className="col-span-full text-center py-20 text-slate-500">
                        No movies found for this category.
                    </div>
                )}
            </div>

            {/* Simple Pagination */}
            <div className="flex justify-center gap-4 mt-12">
                {currentPage > 1 && (
                    <Link href={`/browse?genre=${selectedGenre}&page=${currentPage - 1}`}>
                        <Button variant="outline" className="border-white/20 text-white rounded-full">Previous</Button>
                    </Link>
                )}
                <span className="flex items-center text-slate-400 text-sm">
                    Page {currentPage} of {Math.ceil(total / limit)}
                </span>
                {movies.length === limit && (
                    <Link href={`/browse?genre=${selectedGenre}&page=${currentPage + 1}`}>
                        <Button variant="outline" className="border-white/20 text-white rounded-full">Next</Button>
                    </Link>
                )}
            </div>
        </div>
    );
}
