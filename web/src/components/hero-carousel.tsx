"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Play, Info, Star } from "lucide-react";

interface Movie {
    movieId: number;
    title: string;
    genres: string[];
    year?: number;
    rating?: number;
    posterUrl?: string; // We use posterUrl for hero background in this demo
    description?: string; // Missing in CSV, simplified
}

export function HeroCarousel({ movies }: { movies: Movie[] }) {
    const [index, setIndex] = useState(0);

    // Auto-rotate
    useEffect(() => {
        const timer = setInterval(() => {
            setIndex((prev) => (prev + 1) % movies.length);
        }, 8000);
        return () => clearInterval(timer);
    }, [movies.length]);

    if (!movies || movies.length === 0) return null;

    const movie = movies[index];

    return (
        <div className="relative w-full h-[70vh] min-h-[500px] overflow-hidden">
            <AnimatePresence mode="wait">
                <motion.div
                    key={movie.movieId}
                    className="absolute inset-0"
                    initial={{ opacity: 0, scale: 1.1 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.5 }}
                >
                    {/* Background Image / Gradient Fallback */}
                    <div className="absolute inset-0 bg-midnight-900" />
                    {/* In real app, use backdropUrl */}
                    {movie.posterUrl && (
                        <Image
                            src={movie.posterUrl}
                            alt={movie.title}
                            fill
                            className="object-cover opacity-60 blur-sm scale-110"
                            priority
                        />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-r from-midnight-950 via-midnight-950/80 to-transparent" />
                    <div className="absolute inset-0 bg-gradient-to-t from-midnight-950 via-transparent to-transparent" />
                </motion.div>
            </AnimatePresence>

            <div className="relative z-10 container mx-auto px-4 h-full flex flex-col justify-center">
                <motion.div
                    key={movie.movieId + "content"}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.8 }}
                    className="max-w-2xl"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <span className="bg-gold-500 text-midnight-950 text-xs font-bold px-2 py-1 rounded-sm uppercase tracking-wide">
                            Featured
                        </span>
                        <div className="flex items-center gap-1 text-gold-400 text-sm font-medium">
                            <Star className="w-4 h-4 fill-gold-400" />
                            {movie.rating?.toFixed(1)} Rating
                        </div>
                        <span className="text-slate-300 text-sm">{movie.year}</span>
                    </div>

                    <h1 className="text-5xl md:text-7xl font-serif font-bold text-white mb-4 leading-tight text-glow">
                        {movie.title}
                    </h1>

                    <div className="flex flex-wrap gap-2 mb-8">
                        {movie.genres.map((g) => (
                            <span key={g} className="text-slate-300 text-sm border border-white/20 px-3 py-1 rounded-full backdrop-blur-sm">
                                {g}
                            </span>
                        ))}
                    </div>

                    <div className="flex gap-4">
                        <Button size="lg" className="bg-gold-500 hover:bg-gold-400 text-midnight-950 font-bold rounded-full px-8 text-lg shadow-[0_0_20px_-5px_var(--color-gold-500)] hover:scale-105 transition-transform">
                            <Play className="w-5 h-5 mr-2 fill-current" /> Watch Now
                        </Button>
                        <Link href={`/movie/${movie.movieId}`}>
                            <Button size="lg" variant="outline" className="border-white/20 hover:bg-white/10 text-white rounded-full px-8 text-lg backdrop-blur-sm">
                                <Info className="w-5 h-5 mr-2" /> More Info
                            </Button>
                        </Link>
                    </div>
                </motion.div>
            </div>

            {/* Indicators */}
            <div className="absolute bottom-8 right-8 flex gap-2 z-20">
                {movies.map((_, i) => (
                    <button
                        key={i}
                        onClick={() => setIndex(i)}
                        className={`w-2 h-2 rounded-full transition-all duration-300 ${i === index ? "w-8 bg-gold-500 shadow-glow" : "bg-white/30 hover:bg-white/50"
                            }`}
                    />
                ))}
            </div>
        </div>
    );
}
