"use client";

import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { MovieCard } from "./movie-card";
import { Button } from "@/components/ui/button";

interface Movie {
    movieId: number;
    title: string;
    genres: string[];
    year?: number;
    rating?: number;
    posterUrl?: string;
}

interface MovieRowProps {
    title: string;
    movies: Movie[];
}

export function MovieRow({ title, movies }: MovieRowProps) {
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    const scroll = (direction: "left" | "right") => {
        if (scrollContainerRef.current) {
            const { current } = scrollContainerRef;
            const scrollAmount = direction === "left" ? -800 : 800;
            current.scrollBy({ left: scrollAmount, behavior: "smooth" });
        }
    };

    if (!movies || movies.length === 0) return null;

    return (
        <div className="py-8 relative group">
            <div className="container mx-auto px-4 mb-4 flex items-end justify-between">
                <h2 className="text-2xl md:text-3xl font-serif font-bold text-white relative pl-4">
                    <span className="absolute left-0 top-1 bottom-1 w-1 bg-gold-500 rounded-full" />
                    {title}
                </h2>
                <a href="/browse" className="text-gold-500 text-sm font-medium hover:text-gold-400 transition-colors">
                    View All
                </a>
            </div>

            <div className="relative">
                <div
                    ref={scrollContainerRef}
                    className="flex gap-4 overflow-x-auto pb-8 pt-4 px-4 snap-x snap-mandatory scrollbar-hide container mx-auto"
                    style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
                >
                    {movies.map((movie) => (
                        <div key={movie.movieId} className="snap-start">
                            <MovieCard movie={movie} />
                        </div>
                    ))}
                </div>

                {/* Scroll Buttons */}
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute left-4 top-1/2 -translate-y-1/2 z-20 bg-midnight-950/80 text-white hover:bg-midnight-900/90 hover:text-gold-500 rounded-full w-12 h-12 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-0"
                    onClick={() => scroll("left")}
                >
                    <ChevronLeft className="w-8 h-8" />
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-4 top-1/2 -translate-y-1/2 z-20 bg-midnight-950/80 text-white hover:bg-midnight-900/90 hover:text-gold-500 rounded-full w-12 h-12 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => scroll("right")}
                >
                    <ChevronRight className="w-8 h-8" />
                </Button>

                {/* Fade edges */}
                <div className="absolute top-0 bottom-0 left-0 w-12 bg-gradient-to-r from-midnight-950 to-transparent pointer-events-none" />
                <div className="absolute top-0 bottom-0 right-0 w-12 bg-gradient-to-l from-midnight-950 to-transparent pointer-events-none" />
            </div>
        </div>
    );
}
