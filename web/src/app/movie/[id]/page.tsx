import { notFound } from "next/navigation";
import Image from "next/image";
import { getMovieById, getSimilarMovies } from "@/lib/movielens";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Star, Play, Plus, Share2 } from "lucide-react";
import { MovieRow } from "@/components/movie-row";
import { MovieActions } from "@/components/movie-actions";

interface PageProps {
    params: Promise<{ id: string }>;
}

export default async function MovieDetailsPage({ params }: PageProps) {
    const { id } = await params;
    const movieId = parseInt(id);

    if (isNaN(movieId)) return notFound();

    const movie = await getMovieById(movieId);
    if (!movie) return notFound();

    const similarMovies = await getSimilarMovies(movieId, 10);

    return (
        <div className="min-h-screen bg-midnight-950">
            {/* Hero Section */}
            <div className="relative h-[60vh] w-full">
                {movie.posterUrl && (
                    <Image
                        src={movie.posterUrl}
                        alt={movie.title}
                        fill
                        className="object-cover opacity-30 blur-sm"
                    />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-midnight-950 via-midnight-950/60 to-transparent" />

                <div className="absolute bottom-0 left-0 right-0 container mx-auto px-4 pb-12 flex flex-col md:flex-row gap-8 items-end">
                    {/* Poster */}
                    <div className="relative w-48 h-72 md:w-64 md:h-96 flex-shrink-0 rounded-xl overflow-hidden shadow-2xl border border-white/10 hidden md:block">
                        {movie.posterUrl ? (
                            <Image src={movie.posterUrl} alt={movie.title} fill className="object-cover" />
                        ) : (
                            <div className="w-full h-full bg-midnight-800 flex items-center justify-center text-slate-500">No Image</div>
                        )}
                    </div>

                    <div className="flex-1 space-y-4 mb-4">
                        <h1 className="text-4xl md:text-6xl font-serif font-bold text-white text-glow">{movie.title}</h1>

                        <div className="flex flex-wrap items-center gap-4 text-sm md:text-base text-slate-300">
                            <span className="font-bold text-white">{movie.year}</span>
                            <span className="w-1 h-1 rounded-full bg-slate-500" />
                            <div className="flex items-center gap-1 text-gold-400">
                                <Star className="w-4 h-4 fill-gold-400" />
                                <span className="font-bold text-lg">{movie.rating?.toFixed(1)}</span>
                                <span className="text-slate-500 text-xs">({movie.voteCount} votes)</span>
                            </div>
                        </div>

                        <div className="flex flex-wrap gap-2">
                            {movie.genres.map(g => (
                                <Badge key={g} variant="outline" className="border-white/20 text-slate-200 backdrop-blur-md">
                                    {g}
                                </Badge>
                            ))}
                        </div>

                        <p className="max-w-xl text-slate-300 leading-relaxed text-lg">
                            {/* Description is not in MovieLens dataset, using placeholder */}
                            Experience the cinematic journey of {movie.title}. A masterpiece defined by its genre-defying storytelling and memorable characters.
                        </p>

                        <MovieActions movie={movie} />
                    </div>
                </div>
            </div>

            {/* Similar Movies */}
            <div className="container mx-auto px-4 py-12">
                <MovieRow title={`Because you liked ${movie.title}`} movies={similarMovies} />
            </div>
        </div>
    );
}
