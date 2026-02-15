"use client";

import Link from "next/link";
import { Search, Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Navbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-midnight-950/80 backdrop-blur-md border-b border-white/10">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 group">
                    <Film className="w-8 h-8 text-gold-500 transition-transform group-hover:scale-110" />
                    <span className="text-2xl font-serif font-bold text-white tracking-wide">
                        Magic<span className="text-gold-500">Stream</span>
                    </span>
                </Link>

                <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
                    <Link href="/" className="hover:text-gold-400 transition-colors">Home</Link>
                    <Link href="/browse" className="hover:text-gold-400 transition-colors">Browse</Link>
                    <Link href="/trending" className="hover:text-gold-400 transition-colors">Trending</Link>
                    <Link href="/my-list" className="hover:text-gold-400 transition-colors">My List</Link>
                </div>

                <div className="flex items-center gap-4">
                    <div className="relative hidden sm:block">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <Input
                            type="search"
                            placeholder="Search movies..."
                            className="pl-10 bg-midnight-900/50 border-white/10 text-white placeholder:text-slate-500 focus-visible:ring-gold-500/50 rounded-full w-64 focus-visible:bg-midnight-800 transition-all"
                        />
                    </div>
                    <Button variant="ghost" className="text-gold-400 hover:text-gold-300 hover:bg-gold-500/10 rounded-full">
                        Login
                    </Button>
                    <Button className="bg-gold-500 hover:bg-gold-400 text-midnight-950 font-semibold rounded-full shadow-[0_0_15px_-3px_var(--color-gold-500)] hover:shadow-[0_0_20px_0_var(--color-gold-500)] transition-all">
                        Sign Up
                    </Button>
                </div>
            </div>
        </nav>
    );
}
