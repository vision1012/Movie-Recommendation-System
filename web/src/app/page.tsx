import { getTrendingMovies, getMovies, getMovieById } from "@/lib/movielens";
import { fetchRecommendationsDirect } from "@/lib/api";
import { HeroCarousel } from "@/components/hero-carousel";
import { MovieRow } from "@/components/movie-row";

export default async function Home() {
  // Parallel data fetching for performance
  const [
    trending,
    topPickIds,
    actionMovies,
    comedyMovies,
    familyMovies,
    scifiMovies
  ] = await Promise.all([
    getTrendingMovies(5), // 5 for hero carousel
    fetchRecommendationsDirect(1, 15), // "Top Picks" from Python Backend
    getMovies(1, 15, undefined, 'Action'),
    getMovies(1, 15, undefined, 'Comedy'),
    getMovies(1, 15, undefined, 'Children'),
    getMovies(1, 15, undefined, 'Sci-Fi')
  ]);

  // Hydrate Top Picks
  const topPickedMovies = (await Promise.all(
    topPickIds.map(async (id) => await getMovieById(id))
  )).filter(m => m !== undefined);

  return (
    <div className="min-h-screen pb-20 overflow-x-hidden bg-midnight-950">
      <HeroCarousel movies={trending} />

      <div className="-mt-32 relative z-20 pl-4 md:pl-12 space-y-8">
        <MovieRow title="Trending Now" movies={trending} />
        <MovieRow title="Top Picks For You" movies={topPickedMovies} />
        <MovieRow title="Action Thrillers" movies={actionMovies.data} />
        <MovieRow title="Comedies" movies={comedyMovies.data} />
        <MovieRow title="Family & Children" movies={familyMovies.data} />
        <MovieRow title="Sci-Fi Worlds" movies={scifiMovies.data} />
      </div>
    </div>
  );
}
