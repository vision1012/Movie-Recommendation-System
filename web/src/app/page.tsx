import { getTrendingMovies, getMovies } from "@/lib/movielens";
import { HeroCarousel } from "@/components/hero-carousel";
import { MovieRow } from "@/components/movie-row";

export default async function Home() {
  // Parallel data fetching for performance
  const [
    trending,
    topRated,
    actionMovies,
    comedyMovies,
    familyMovies,
    scifiMovies
  ] = await Promise.all([
    getTrendingMovies(5), // 5 for hero carousel
    getMovies(1, 15), // "Top Rated" (default sort in getMovies is effectively ID based for now, but we can assume it's general list)
    getMovies(1, 15, undefined, 'Action'),
    getMovies(1, 15, undefined, 'Comedy'),
    getMovies(1, 15, undefined, 'Children'), // MovieLens uses 'Children' usually
    getMovies(1, 15, undefined, 'Sci-Fi')
  ]);

  return (
    <div className="min-h-screen pb-20 overflow-x-hidden">
      <HeroCarousel movies={trending} />

      <div className="-mt-32 relative z-20 pl-4 md:pl-8 space-y-4">
        <MovieRow title="Trending Now" movies={trending} />
        <MovieRow title="Top Picks For You" movies={topRated.data} />
        <MovieRow title="High Octane Action" movies={actionMovies.data} />
        <MovieRow title="Laugh Out Loud" movies={comedyMovies.data} />
        <MovieRow title="Family Favorites" movies={familyMovies.data} />
        <MovieRow title="Sci-Fi Spectacles" movies={scifiMovies.data} />
      </div>
    </div>
  );
}
