# Fake Account Detector — Project Summary

## Overview

Fake Account Detector is a Flask web application that screens Instagram accounts for potentially fake or suspicious behaviour. It combines manual input, optional Playwright-based Instagram fetching, feature engineering, a scikit-learn Random Forest model, and a risk-verdict dashboard.

It is a screening aid, not an identity-verification or moderation system.

## User workflow

1. Open `http://127.0.0.1:5000`.
2. Enter an Instagram username.
3. Click **Fetch Data**, or enter values manually.
4. Review/edit bio, followers, following, posts, and profile-picture status.
5. Click **Analyze Account**.
6. Review the prediction, confidence, risk score, verdict, and reasoning.

## Architecture

```text
Browser
  -> Flask routes in app.py
      -> /api/fetch-instagram: Playwright + BeautifulSoup parser
      -> /api/analyze: feature extraction -> saved Random Forest -> verdict
```

## Repository map

| Path | Responsibility |
|---|---|
| `app.py` | Flask app, model loading, routes, API responses |
| `model.py` | Dataset normalization, model training, evaluation, serialization |
| `utils/features.py` | Runtime feature engineering |
| `utils/instagram_fetch.py` | Instagram browser fetch and profile parsing |
| `utils/verdict.py` | Risk score and verdict calculation |
| `templates/index.html` | Dashboard markup |
| `static/app.js` | API calls, form population, result rendering |
| `static/style.css` | Dark responsive UI styling |
| `data/instagram_dataset.csv` | Training dataset |
| `csv/` | Original/all/fake/real dataset exports |
| `model/account_model.pkl` | Serialized pipeline and feature order |
| `model/metrics.json` | Stored evaluation metrics |
| `tests/` | Parser and frontend regression tests |
| `pyproject.toml` | Python dependencies and project metadata |
| `uv.lock` | Locked dependency resolution |

## Backend API

### `GET /`

Renders the main dashboard.

### `POST /api/fetch-instagram`

Request:

```json
{"username":"example_user","session_id":null,"headless":true}
```

Returns normalized profile data including:

```json
{
  "success": true,
  "profile": {
    "username": "example_user",
    "full_name": "Example User",
    "bio": "Profile biography",
    "followers_count": 293,
    "following_count": 222,
    "media_count": 3,
    "is_private": false,
    "profile_pic_url": "https://...",
    "is_verified": false,
    "data_source": "json",
    "warnings": []
  }
}
```

The fetcher uses nested JSON/GraphQL data first, then rendered profile markup and Open Graph metadata. Post counts can come from `media_count`, GraphQL timeline counts/edges, Open Graph `Posts` text, rendered `/p/`, `/reel/`, or `/tv/` links, and live Playwright DOM links. It de-duplicates post URLs and preserves bio emoji/newlines.

### `POST /api/analyze`

Request:

```json
{
  "username":"example_user",
  "bio":"Profile biography",
  "followers_count":293,
  "following_count":222,
  "media_count":3,
  "has_profile_pic":1
}
```

The route extracts features, calls `predict_proba()`, treats class-probability index `1` as the fake probability, applies a `0.5` fake/real threshold, and calculates the final verdict.

Example response:

```json
{
  "success": true,
  "prediction": "Fake",
  "confidence": 0.84,
  "verdict": "High Risk Fake",
  "risk_score": 84,
  "reasoning": "Model strongly predicts this account is fake."
}
```

### `GET /health`

Returns `{"status":"ok"}`.

## Machine-learning pipeline

Training is implemented in `model.py`.

### Features

| Feature | Meaning |
|---|---|
| `followers_count` | Followers |
| `following_count` | Following |
| `media_count` | Posts/media |
| `has_profile_pic` | Numeric profile-picture flag |
| `bio_length` | Trimmed bio character length |
| `username_length` | Username character length |
| `digit_count_in_username` | Numeric characters in username |
| `followers_following_ratio` | Followers divided by following plus one |

### Training configuration

- Model: `RandomForestClassifier`
- Estimators: `200`
- `random_state`: `42`
- `class_weight`: `balanced`
- Missing values: median `SimpleImputer`
- Split: 80% train / 20% test
- Stratification: enabled

Dataset normalization supports aliases such as `userFollowerCount`, `userFollowingCount`, `userMediaCount`, `userHasProfilPic`, `userBiographyLength`, `usernameLength`, `usernameDigitCount`, and `isFake`.

### Current metrics

`model/metrics.json` reports:

| Metric | Value |
|---|---:|
| Accuracy | 0.9707 |
| Precision | 0.9714 |
| Recall | 0.8500 |
| F1 | 0.9067 |

The training dataset has 1,194 rows: 994 real and 200 fake. `csv/allAccountData.csv` has 1,195 rows, so it differs from the training input by one row.

## Verdict logic

`utils/verdict.py` converts model output into a 0–100 risk score:

| Prediction/confidence | Verdict |
|---|---|
| Fake, confidence `>= 0.80` | High Risk Fake |
| Fake, confidence `0.60–0.79` | Suspicious |
| Fake, confidence `< 0.60` | Needs Review |
| Real, confidence `>= 0.75` | Likely Genuine |
| Real, confidence `< 0.75` | Needs Review |

Confidence is model certainty, not proof of authenticity.

## Frontend

`templates/index.html` provides username fetching, editable profile fields, manual override, and result cards. `static/app.js` validates usernames, calls both APIs, preserves zero values, clears stale results, renders warnings safely with DOM APIs, and displays verdict styling. `static/style.css` provides a dark responsive layout with mobile support.

## Tests and checks

Current regression coverage includes:

- Nested Instagram JSON extraction
- Emoji and multiline bios
- Correct follower/following values
- Rendered header counts
- Open Graph metadata fallback
- Nested, relative, absolute, and duplicate post links
- Zero JSON/GraphQL post-count recovery
- Live rendered-post-count fallback
- Positive JSON count precedence
- Safe frontend rendering and stale-result clearing

Verified commands:

```powershell
uv run python -m unittest discover -s tests -p "test*.py"
uv run python -m py_compile utils/instagram_fetch.py tests/test_instagram_fetch.py
node tests/test_profile_ui.cjs
node --check static/app.js
git diff --check
```

The current Python parser suite contains 10 passing tests, and the frontend smoke test passes.

## Setup and operation

```powershell
uv sync
python -m playwright install
uv run python model.py       # optional: retrain
uv run python app.py
```

Open `http://127.0.0.1:5000`.

Because `app.py` runs with `debug=False`, source changes require a complete Flask restart before retesting.

## Strengths

- Clear separation between fetching, features, inference, verdicts, and UI
- Feature order is stored with the model artifact
- Manual override handles incomplete or incorrect scraped values
- Multiple Instagram response formats are supported
- Recent parser failures have regression coverage
- Frontend fetched values are rendered safely

## Limitations and risks

1. Instagram scraping is fragile and can be affected by markup changes, login requirements, rate limits, and anti-bot systems.
2. The project does not use an official Instagram API.
3. The model uses limited metadata and does not assess images, engagement quality, account age, or follower networks.
4. The dataset is imbalanced toward real accounts.
5. Metrics are from one train/test split; cross-validation and a separate holdout set would be stronger.
6. The Flask fetch route returns a generic error instead of exposing the detailed parser failure.
7. The serialized model is sensitive to Python and scikit-learn versions.
8. Visible grid counts can undercount lazy-loaded posts; complete metadata totals should be preferred.
9. Automated collection should be reviewed for Instagram terms, privacy, and applicable law.

## Recommended next improvements

### High priority

- Add mocked Flask API integration tests.
- Return structured scraper error codes and safer user-facing explanations.
- Display the data source and data-confidence state in the UI.
- Add a model-readiness check to `/health`.

### Medium priority

- Add cross-validation, confusion matrices, and model version metadata.
- Validate negative and implausibly large numeric inputs.
- Document or consolidate the duplicate CSV datasets.
- Add official API or approved data-source support where available.

### Long term

- Add account age, posting frequency, engagement, and follower-quality features.
- Provide explainability through feature importance and per-account signals.
- Add authentication, rate limiting, audit logging, and monitoring before deployment.

## Overall assessment

This is a functional end-to-end prototype: a user can fetch or enter profile metadata, run a saved ML classifier, and receive an actionable risk-oriented result. The structure is suitable for demonstration or academic work. Production use would require a more reliable data source, stronger evaluation, richer features, monitoring, and formal privacy/model-governance controls.
