# Movie Recommendation System

A production-minded recommendation system with baselines (popularity, genre, item-item), implicit ALS, and a hybrid model. Includes a FastAPI service for easy integration with streaming apps.

## Features

- **Recommendation types**: Personalized feed + "Because you watched X" (item-to-item)
- **Models**: Popularity, genre-based, item-item CF, implicit ALS, hybrid (CF + content)
- **Cold start**: Genre-based + popularity fallback for new users
- **Constraints**: Exclude watched, diversity/novelty, optional genre/year filters
- **Metrics**: NDCG@K, Recall@K, Precision@K
- **API**: FastAPI with `/health`, `/recommend`, `/similar`

## Setup

```bash
cd "Movie Recommendation System"
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Dataset

**Option A: Synthetic data** (default)

No download needed. Config uses synthetic data by default.

**Option B: MovieLens**

1. Download [MovieLens](https://grouplens.org/datasets/movielens/) (e.g. ml-25m)
2. Place `ratings.csv` and `movies.csv` in `data/raw/`
3. Set `data.source: movielens` in `configs/config.yaml`

## Commands

### 1. Data pipeline (ingest + preprocess)

```bash
python scripts/run_data_pipeline.py
```

Output: `data/processed/train.parquet`, `val.parquet`, `test.parquet`, `item_metadata.parquet`, `item_genre_matrix.parquet`

### 2. Training

```bash
python scripts/run_training.py
```

Output: `models/popularity.joblib`, `genre.joblib`, `item_item.joblib`, `implicit_als.joblib`, `hybrid.joblib`

### 3. Evaluation

```bash
python scripts/run_evaluation.py
```

Output: `reports/evaluation_report.json`

### 4. Serve API

```bash
python -m api.main
# or
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Examples

### Health check

```bash
curl http://localhost:8000/health
```

### Personalized recommendations

```bash
curl "http://localhost:8000/recommend?user_id=1&k=10"
```

With filters:

```bash
curl "http://localhost:8000/recommend?user_id=1&k=10&genre_filter=Sci-Fi,Action&year_min=2010"
```

### Similar items (because-you-watched)

```bash
curl "http://localhost:8000/similar?item_id=1&k=5"
```

### Response format

**GET /recommend**

```json
{
  "user_id": "1",
  "recommendations": [
    {
      "movie_id": 456,
      "title": "Inception",
      "genres": ["Sci-Fi", "Action"],
      "year": 2010,
      "score": 0.92,
      "reason": "collaborative_filtering",
      "reason_detail": "Based on your viewing history"
    }
  ]
}
```

**GET /similar**

```json
{
  "item_id": "1",
  "similar_items": [
    {
      "movie_id": 789,
      "title": "Interstellar",
      "genres": ["Sci-Fi", "Drama"],
      "year": 2014,
      "similarity_score": 0.95
    }
  ]
}
```

## Integration with Streaming App

**Inputs to send**

- `user_id`: anonymized user identifier (integer)
- `k`: number of recommendations (default 10)
- Optional: `genre_filter`, `year_min`, `year_max`

**Outputs returned**

- `recommendations`: array of `{movie_id, title, genres, year, reason, reason_detail}`
- `similar_items`: for item-to-item, array of `{movie_id, title, genres, year, similarity_score}`

**Batch updates**

- Retrain nightly: `python scripts/run_data_pipeline.py && python scripts/run_training.py`
- Cron example: `0 2 * * * cd /path/to/project && .venv/bin/python scripts/run_data_pipeline.py && .venv/bin/python scripts/run_training.py`

## Project Structure

```
├── api/
│   └── main.py              # FastAPI app
├── configs/
│   └── config.yaml
├── data/
│   ├── raw/                 # ratings.csv, movies.csv
│   └── processed/           # parquet outputs
├── docs/
│   └── ARCHITECTURE.md
├── models/                  # trained artifacts
├── reports/                 # evaluation reports
├── scripts/
│   ├── run_data_pipeline.py
│   ├── run_training.py
│   └── run_evaluation.py
├── src/
│   ├── config.py
│   ├── data/
│   │   ├── ingest.py
│   │   ├── preprocess.py
│   │   └── pipeline.py
│   ├── models/
│   │   ├── baselines.py
│   │   ├── implicit_als.py
│   │   └── hybrid.py
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── evaluate.py
│   └── inference/
│       └── predictor.py
├── tests/
└── requirements.txt
```

## Tradeoffs & Future Improvements

| Current | Improve Later |
|---------|---------------|
| Implicit ALS | Two-tower / neural MF |
| Batch updates | Online learning |
| In-memory cache | Redis for multi-instance |
| Parquet feature store | Feast or similar |
| Genre-only content | Tag/synopsis embeddings |
