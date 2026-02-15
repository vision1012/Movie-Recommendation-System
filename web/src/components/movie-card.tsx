"use client";

import Image from "next/image";
import Link from "next/link";
import { Star } from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import type { Movie } from "@/lib/movielens"; // We'll need to share types properly

// Temporary interface until we export it from a shared location accessible to client
interface MovieProps {
    movieId: number;
    title: string;
    genres: string[];
    year?: number;
    rating?: number;
    posterUrl?: string;
}

export function MovieCard({ movie }: { movie: MovieProps }) {
    return (
        <Link href={`/movie/${movie.movieId}`}>
            <motion.div
                className="group relative flex-shrink-0 w-[200px] cursor-pointer"
                whileHover={{ y: -10 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
                <div className="relative aspect-[2/3] rounded-2xl overflow-hidden shadow-lg border border-white/5 bg-midnight-800 movie-card-hover">
                    {movie.posterUrl ? (
                        <Image
                            src={movie.posterUrl}
                            alt={movie.title}
                            fill
                            className="object-cover transition-transform duration-500 group-hover:scale-110"
                            sizes="200px"
                            unoptimized // Since we might use external URLs
                        />
                    ) : (
                        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-midnight-800 text-slate-400">
                            <span className="text-4xl mb-2">🎬</span>
                            <span className="text-xs">{movie.title}</span>
                        </div>
                    )}

                    <div className="absolute inset-0 bg-gradient-to-t from-midnight-950 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                    <div className="absolute bottom-0 left-0 right-0 p-4 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                        <h3 className="text-white font-bold line-clamp-2 leading-tight mb-1 font-serif text-shadow-sm">
                            {movie.title}
                        </h3>
                        <div className="flex items-center gap-2 text-xs text-gold-400 mb-2">
                            <span className="flex items-center gap-1 bg-black/50 px-1.5 py-0.5 rounded-md backdrop-blur-sm">
                                <Star className="w-3 h-3 fill-gold-400" /> {movie.rating?.toFixed(1) || "N/A"}
                            </span>
                            <span className="text-slate-300">{movie.year}</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {movie.genres.slice(0, 2).map(g => (
                                <Badge key={g} variant="secondary" className="text-[10px] h-5 bg-white/10 hover:bg-white/20 text-white backdrop-blur-md border-0">
                                    {g}
                                </Badge>
                            ))}
                        </div>
                    </div>
                </div>
            </motion.div>
        </Link>
    );
}
