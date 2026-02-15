# Movie Recommendation System – Architecture & Implementation Plan

## 1. Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           MOVIE RECOMMENDATION SYSTEM                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │   Config    │
                                    │ (YAML/JSON) │
                                    └──────┬──────┘
                                           │
     ┌─────────────────────────────────────┼─────────────────────────────────────┐
     │                                     │                                     │
     ▼                                     ▼                                     ▼
┌─────────┐                        ┌──────────────┐                        ┌─────────────┐
│  Data   │                        │   Training   │                        │   API       │
│ Pipeline│                        │   Pipeline   │                        │  (FastAPI)  │
└────┬────┘                        └──────┬───────┘                        └──────┬──────┘
     │                                    │                                      │
     │  ┌─────────────┐                   │  ┌────────────────┐                  │
     ├──│ Ingestion   │                   ├──│ Baseline: Pop   │                  │
     │  │ (CSV/Parquet)│                  │  │ Baseline: Genre │                  │
     │  └─────────────┘                   │  │ Item-Item (CF)  │                  │
     │  ┌─────────────┐                   │  │ Implicit ALS    │                  │
     ├──│ Preprocess  │                   │  │ Hybrid (CF+CB)  │                  │
     │  │ Time split  │                   │  └────────────────┘                  │
     │  │ Recency wt  │                   │  ┌────────────────┐                  │
     │  └─────────────┘                   ├──│ Evaluation     │                  │
     │  ┌─────────────┐                   │  │ NDCG/Recall/   │                  │
     └──│ Feature     │                   │  │ Precision@K    │                  │
        │ Store Lite  │                   │  └────────────────┘                  │
        └──────┬──────┘                   └──────┬───────────────┘                │
               │                                 │                                │
               │         ┌───────────────────────┼───────────────────────┐        │
               │         │                       │                       │        │
               ▼         ▼                       ▼                       ▼        │
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
        │  Artifacts/  │  │  Parquet/    │  │  Model       │  │ Inference       │ │
        │  models/     │  │  features    │  │  Pickles     │  │ Service         │ │
        └──────────────┘  └──────────────┘  └──────────────┘  └────────┬────────┘ │
                                                                       │          │
        ┌──────────────────────────────────────────────────────────────┘          │
        │                                                                         │
        ▼                                                                         ▼
  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────┐
  │ /health     │  │ /recommend      │  │ /similar        │
  │ /recommend  │  │ user_id, k,     │  │ item_id, k      │
  │ /similar    │  │ filters, etc.   │  │                 │
  └─────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 2. Component Summary

| Component        | Purpose                                                                 |
|------------------|-------------------------------------------------------------------------|
| **Config**       | YAML config: paths, seeds, model params, split dates                    |
| **Data pipeline**| Ingest MovieLens (or synthetic), preprocess, time-split, feature store  |
| **Training**     | Baselines (popularity, genre, item-item), implicit ALS, hybrid          |
| **Evaluation**   | NDCG@K, Recall@K, Precision@K on held-out set (time-based)              |
| **Inference**    | Load models, apply filters (exclude watched), diversity, cache          |
| **API**          | FastAPI: health, recommend (IDs + metadata + reasons), similar items    |
| **Persistence**  | `models/`, `data/processed/`, parquet feature store                     |

---

## 3. Data Flow

1. **Raw** → `data/raw/` (ratings.csv, movies.csv, tags.csv)
2. **Processed** → `data/processed/` (interactions.parquet, item_metadata.parquet)
3. **Split** → train/val/test by timestamp (e.g. 70/15/15)
4. **Features** → genre encoding, popularity scores, recency weights
5. **Models** → saved to `models/` (pickle/joblib)
6. **API** → loads artifacts at startup, serves from memory + cache

---

## 4. Implementation Phases

| Phase | Scope | Outputs |
|-------|-------|---------|
| **1** | Repo structure, config, data ingestion, preprocessing | `config.yaml`, `src/data/`, synthetic/MovieLens support |
| **2** | Training pipeline | Baselines + implicit ALS, hybrid, saved artifacts |
| **3** | Evaluation | NDCG/Recall/Precision@K report |
| **4** | Inference | Predictors with exclude-watched, diversity, caching |
| **5** | API | FastAPI with /health, /recommend, /similar |
| **6** | Persistence + README | Feature store lite, run commands, example curls |

---

## 5. Tradeoffs & Future Improvements

| Decision | Tradeoff | Improve Later |
|----------|----------|---------------|
| Implicit ALS | Fast, scalable; no content in core | Add two-tower or neural MF |
| Batch updates | Simpler; no real-time | Add online learning / approximate updates |
| In-memory cache | Low latency; memory-bound | Redis/Memcached for multi-instance |
| Parquet feature store | Simple, portable | Dedicated feature store (Feast, etc.) |
| Genre-only content | Quick cold start | Add embeddings for tags/synopsis |

---

## 6. API Contract

### `GET /recommend?user_id={id}&k={10}`

**Response:**
```json
{
  "user_id": "123",
  "recommendations": [
    {
      "movie_id": "456",
      "title": "Inception",
      "genres": ["Sci-Fi", "Action"],
      "year": 2010,
      "reason": "similar_to_watched",
      "reason_detail": "Because you watched Interstellar"
    }
  ]
}
```

### `GET /similar?item_id={id}&k={10}`

**Response:**
```json
{
  "item_id": "456",
  "similar_items": [
    {
      "movie_id": "789",
      "title": "Interstellar",
      "genres": ["Sci-Fi", "Drama"],
      "similarity_score": 0.92
    }
  ]
}
```
