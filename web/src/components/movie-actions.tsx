"use client";

import { Button } from "@/components/ui/button";
import { Play, Plus, Check, Share2 } from "lucide-react";
import { useMyList } from "@/hooks/use-my-list";

interface Movie {
    movieId: number;
    title: string;
    posterUrl?: string;
    rating?: number;
    year?: number;
    genres: string[];
}

export function MovieActions({ movie }: { movie: Movie }) {
    const { isInList, addMovie, removeMovie } = useMyList();
    const inList = isInList(movie.movieId);

    const toggleList = () => {
        if (inList) {
            removeMovie(movie.movieId);
        } else {
            addMovie(movie);
        }
    };

    return (
        <div className="flex flex-wrap gap-4 pt-4">
            <Button size="lg" className="bg-gold-500 hover:bg-gold-400 text-midnight-950 font-bold px-8 shadow-glow-gold rounded-full transition-transform active:scale-95">
                <Play className="w-5 h-5 mr-2 fill-current" /> Play Movie
            </Button>

            <Button
                size="lg"
                variant="secondary"
                onClick={toggleList}
                className={`backdrop-blur-md border border-white/10 rounded-full transition-all active:scale-95 ${inList ? "bg-gold-500/20 text-gold-500 border-gold-500/50" : "bg-white/10 hover:bg-white/20 text-white"}`}
            >
                {inList ? <Check className="w-5 h-5 mr-2" /> : <Plus className="w-5 h-5 mr-2" />}
                {inList ? "In My List" : "My List"}
            </Button>

            <Button size="icon" variant="ghost" className="rounded-full text-slate-400 hover:text-white hover:bg-white/10 transition-colors">
                <Share2 className="w-5 h-5" />
            </Button>
        </div>
    );
}
