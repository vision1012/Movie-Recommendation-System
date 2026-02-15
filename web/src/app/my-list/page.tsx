"use client";

import { useMyList } from "@/hooks/use-my-list";
import { MovieCard } from "@/components/movie-card";

export default function MyListPage() {
    const { list } = useMyList();

    return (
        <div className="container mx-auto px-4 py-8 min-h-screen">
            <h1 className="text-3xl font-serif font-bold text-white mb-8 border-l-4 border-gold-500 pl-4">My List</h1>

            {list.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
                    {list.map((movie) => (
                        <div key={movie.movieId} className="flex justify-center">
                            <MovieCard movie={movie} />
                        </div>
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                    <p className="text-xl mb-4">Your list is empty.</p>
                    <p className="text-sm">Start adding movies you love or want to watch later!</p>
                </div>
            )}
        </div>
    );
}
