"use client";

import { useState, useEffect } from "react";

interface Movie {
    movieId: number;
    title: string;
    posterUrl?: string;
    rating?: number;
    year?: number;
    genres: string[];
}

export function useMyList() {
    const [list, setList] = useState<Movie[]>([]);

    useEffect(() => {
        const stored = localStorage.getItem("my-list");
        if (stored) {
            try {
                setList(JSON.parse(stored));
            } catch (e) {
                console.error("Failed to parse my-list", e);
            }
        }
    }, []);

    const saveList = (newList: Movie[]) => {
        setList(newList);
        localStorage.setItem("my-list", JSON.stringify(newList));
    };

    const addMovie = (movie: Movie) => {
        if (list.some((m) => m.movieId === movie.movieId)) return;
        saveList([...list, movie]);
    };

    const removeMovie = (movieId: number) => {
        saveList(list.filter((m) => m.movieId !== movieId));
    };

    const isInList = (movieId: number) => {
        return list.some((m) => m.movieId === movieId);
    };

    return { list, addMovie, removeMovie, isInList };
}
