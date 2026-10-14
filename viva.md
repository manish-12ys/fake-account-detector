# Fake Account Detector — Viva Preparation Guide

This document is based on the actual repository code and files in this project. It is meant to help with a practical viva or project defense, not to invent features or describe code that is not present.

## 1. Project overview

### Project title
Fake Account Detector

### Purpose
This project detects whether an Instagram account appears to be fake or real by combining:
- manual user input,
- optional live profile fetching,
- feature engineering,
- a trained Random Forest classifier,
- a verdict engine that converts model output into a risk score and explanation.

### Problem statement
Instagram accounts can be created for spam, impersonation, scams, bot activity, or fake engagement. A quick visual inspection is not always enough. The project tries to provide a lightweight decision-support tool to screen suspicious accounts using measurable account metadata.

### Why this project is needed
In the real world, moderation teams, researchers, and users need a quick signal before trusting an account. A deterministic rule-based or ML-based screening tool helps reduce the effort of manual review.

### Existing system and limitations
The project does not use a database or user authentication. It relies on:
- user-entered fields in a web UI,
- optional browser-based data collection from Instagram,
- a saved ML model trained on a CSV dataset.

This means the system is a screening aid, not a verified identity system. It is useful for triage, not final proof.

### Proposed system and its advantages
The proposed system uses a Flask backend, a simple browser interface, and a trained machine learning model. It can:
- fetch public account metadata from Instagram,
- normalize raw values,
- generate predictive features,
- classify as Fake or Real,
- generate a human-friendly verdict and explanation.

### Main objectives
- Detect suspicious account patterns using account metadata.
- Combine manual and automated data collection.
- Keep the system easy to run locally.
- Show prediction confidence and a risk verdict to the user.
- Provide a web dashboard for quick use.

### Target users
- Social media moderators
- Researchers studying fake accounts
- Developers evaluating ML-based trust screening
- Students learning full-stack + ML integration

### Key features
- Flask web app for analysis
- Live Instagram profile fetch via Playwright
- Feature engineering for metrics such as follower/following ratio and username pattern
- Random Forest classification
- Risk verdict generation
- Clean dashboard with manual override and result display

### Scope and limitations
The project works with profile metadata and does not verify the real identity of a person. It does not implement login, user auth, database persistence, or production-grade moderation workflows.

### Real-world applications
- Account verification screening
- Fraud detection assistance
- Social media moderation support
- Research prototype for detecting suspicious accounts

### Why it is different
This project combines a front-end dashboard, backend ML, browser-based profile retrieval, and an explainable verdict layer in one small app. It is relatively beginner-friendly and practical for demonstration.

## 2. Ready-to-speak viva answers

### 30-second explanation
This project is a Flask-based system that detects suspicious Instagram accounts using machine learning. A user enters profile details or fetches them from Instagram, the app calculates features like follower/following ratio and username length, and a saved Random Forest model predicts whether the account is fake or real. The app then assigns a risk score and verdict such as High Risk Fake or Likely Genuine.

### 1-minute explanation
Fake Account Detector is a beginner-friendly ML project built with Python and Flask. It helps screen Instagram profiles for suspicious behavior using public account metadata such as followers, following, bio length, username characteristics, and profile picture presence. The project uses a trained Random Forest model saved as a serialized pipeline. The app also supports fetching live profile information from Instagram using Playwright. The backend extracts feature values, runs the model, and returns a prediction, confidence score, and risk verdict. The project demonstrates both frontend development and machine learning in one workflow.

### 3-minute explanation
This project is a practical ML-based fake-account screening application. The workflow begins with the user entering an Instagram username or manually filling in fields like bio, followers, following, posts, and profile picture status. The app can also call a Playwright-based scraper to fetch public profile data from an Instagram page. The data is normalized and converted into model features such as follower/following ratio, username length, digit count, bio length, and whether a profile photo exists. These features are passed to a Random Forest model trained in `model.py` using a CSV dataset. The model predicts whether the account is likely real or fake, and the verdict logic in `utils/verdict.py` converts the model confidence into a clear result such as High Risk Fake, Suspicious, Likely Genuine, or Needs Review.

The system is designed as a usability-focused prototype. The backend routes are implemented in `app.py`, while the interface is served by Flask templates and JavaScript. The app is easy to demonstrate because everything is local and the model is saved in `model/account_model.pkl`. However, it is a screening aid and not a definitive identity verification system, especially because Instagram scraping can fail due to privacy settings or anti-bot protections.

## 3. Technology stack and package analysis

| Item | Purpose | Why it was chosen | Where used | Alternative |
|---|---|---|---|---|
| Python 3.14+ | Main programming language | Matches the project runtime and available dependencies | Project code, model training, Flask app | JavaScript/Node.js, Java, C# |
| Flask | Web framework | Simple API and UI hosting | `app.py` | FastAPI, Django |
| scikit-learn | Machine learning framework | Random Forest training and evaluation | `model.py` | XGBoost, LightGBM |
| pandas | Data manipulation | CSV dataset loading and normalization | `model.py` | NumPy-only processing or CSV parsers |
| numpy | Numerical arrays and feature values | Safe numeric data handling | `model.py`, feature logic | Python lists, manual math |
| joblib | Model serialization | Saves trained model artifact | `app.py`, `model.py` | pickle |
| BeautifulSoup4 | HTML parsing | Extracting nested Instagram profile data | `utils/instagram_fetch.py` | regex parsing only |
| Playwright | Browser automation | Fetching public Instagram pages | `utils/instagram_fetch.py` | Selenium, requests + manual scraping |
| requests | HTTP + network calls | Potentially used for fetching or web interactions | Not strongly evidenced in the runtime logic; import not found in project code | `httpx`, urllib |
| joblib | Pickle-like model persistence | Stores trained model + feature order | `app.py` | pickle |
| HTML/CSS/JS | Frontend UI | Makes the app usable in the browser | `templates/index.html`, `static/app.js`, `static/style.css` | React or Vue |
| Git + README + UV | Project workflow | Dependency management and reproducibility | `pyproject.toml`, `uv.lock` | pip, Poetry |

### Direct dependencies actually used in code
These are verified in the repository source:
- Flask
- joblib
- numpy
- pandas
- scikit-learn
- BeautifulSoup4
- Playwright

### Dependencies present in `pyproject.toml` but not clearly used in the source
The following are declared in `pyproject.toml`, but there is no clear evidence in the runtime application code that they are used directly:
- altair
- gunicorn
- impo
- instagramy
- instagrapi
- instaloader
- pillow
- selenium
- webdriver-manager

This does not mean they are wrong or unusable; it simply means they are not clearly used by the actual application logic inspected in this repository.

### Package-by-package explanation

#### Flask
- What it is: A lightweight Python web framework.
- Problem it solves: Routing, request handling, and HTML responses.
- Why needed: The project exposes routes like `/api/analyze` and `/api/fetch-instagram`.
- Where used: `app.py`.
- Example: `@app.route('/api/analyze', methods=['POST'])`.
- If removed: The app would not run as a web service.
- Alternatives: FastAPI, Django.

#### scikit-learn
- What it is: ML library for classification and evaluation.
- Problem it solves: Training classifiers and generating predictions.
- Why needed: The core project is a fake account detector.
- Where used: `model.py`.
- Example: `RandomForestClassifier(...)`.
- If removed: No model training or inference would be possible.
- Alternatives: XGBoost, LightGBM, logistic regression.

#### pandas / numpy
- What it is: Data-analysis libraries.
- Problem they solve: Handling CSVs and numeric features.
- Why needed: Model training uses a dataset and feature vectors.
- Where used: `model.py` and `utils/features.py`.
- Example: `df = pd.read_csv(args.data)` and `np` imports in training code.
- If removed: More manual conversion and data cleaning would be required.
- Alternatives: plain Python lists or PyArrow.

#### joblib
- What it is: Serialization utility for model persistence.
- Problem it solves: Saving trained pipelines to disk.
- Why needed: The app loads the trained model at startup from `model/account_model.pkl`.
- Where used: `app.py` and `model.py`.
- Example: `joblib.dump({...}, model_path)`.
- If removed: The model would need to be retrained or loaded differently.
- Alternatives: `pickle`.

#### BeautifulSoup4
- What it is: HTML/XML parser library.
- Problem it solves: Extracting structured data from page markup.
- Why needed: Instagram HTML contains profile data in nested JSON, metadata, and markup.
- Where used: `utils/instagram_fetch.py`.
- Example: `BeautifulSoup(html_content, 'html.parser')`.
- If removed: HTML parsing would be much harder and less reliable.
- Alternatives: lxml, regex-based parsing.

#### Playwright
- What it is: Browser automation tool.
- Problem it solves: Accessing dynamic web pages that require a browser context.
- Why needed: The project fetches Instagram profiles, which may hide data in generated HTML or browser-rendered DOM.
- Where used: `utils/instagram_fetch.py`.
- Example: `async with async_playwright() as p:`.
- If removed: Real-time scraping would be harder and less robust.
- Alternatives: Selenium, requests only.

## 4. File-by-file explanation

### [app.py](app.py)
Responsibility: Flask app entry point and controller logic.

Important elements:
- `app = Flask(__name__, template_folder='templates', static_folder='static')`
- `BASE_DIR` and `MODEL_PATH`
- `MODEL = data["model"]` and `FEATURE_COLUMNS = data["feature_columns"]`
- Route `/` for UI
- Route `/api/analyze` for classification
- Route `/api/fetch-instagram` for scraping
- Route `/health` for health check

Interaction:
- Loads the serialized model on startup.
- Calls `extract_features()` for predictions.
- Calls `compute_verdict()` for output explanation.
- Uses `fetch_instagram_profile()` for live profile fetch.

Likely viva questions:
- Why is the model loaded at startup?
- What happens if the model file is missing?
- Why is `predict_proba()[0][1]` used?
- Why is the route returning JSON with `success` and `error`?

### [model.py](model.py)
Responsibility: Training pipeline, preprocessing, and model serialization.

Important elements:
- `normalize_columns()` renames aliases such as `userFollowerCount` to standardized names.
- `add_ratio_feature()` calculates `followers_following_ratio`.
- `validate_columns()` ensures required fields exist.
- `Pipeline([...])` with `SimpleImputer` + `RandomForestClassifier`.
- `train_test_split` with `stratify=y`.
- Model saved as `model/account_model.pkl`.

Interaction:
- Reads CSV data from `data/instagram_dataset.csv`.
- Produces a trained model artifact used by `app.py`.

Likely viva questions:
- Why is a training pipeline used instead of training directly on raw columns?
- What is `class_weight='balanced'` doing?
- Why are median imputation and stratified split important?

### [utils/features.py](utils/features.py)
Responsibility: Converts raw user input into model-friendly numeric features.

Important elements:
- `FEATURE_COLUMNS` list
- `extract_features()`
- `features_to_vector()`

This function calculates:
- username length
- digit count in username
- bio length
- follower/following ratio
- numeric counts for followers, following, media, profile picture flag

Interaction:
- Used inside `app.py` before prediction.

Likely viva questions:
- Why is `followers_count / (following_count + 1)` used?
- Why is the `+ 1.0` used in the denominator?
- Why are values converted to float?

### [utils/verdict.py](utils/verdict.py)
Responsibility: Converts model decisions into a user understandable verdict.

Important elements:
- `VerdictResult` dataclass
- `compute_verdict()`

The function maps:
- High fake probability to High Risk Fake / Suspicious / Needs Review
- High real probability to Likely Genuine if confidence is strong

Interaction:
- Called from `app.py` after the model predicts.

Likely viva questions:
- Why is a verdict layer used instead of directly showing the probability?
- Why do real accounts need higher confidence to be considered “Likely Genuine”?

### [utils/instagram_fetch.py](utils/instagram_fetch.py)
Responsibility: Retrieves and normalizes Instagram profile data.

Important concepts:
- `InstagramProfile` dataclass
- `_find_profile_json()` searches nested JSON and GraphQL structures
- `_meta_profile()` reads OG metadata from HTML
- `_rendered_profile_values()` extracts profile-scoped values from the browser DOM
- `fetch_instagram_profile()` is the main public function

Interaction:
- Used by `app.py` route `/api/fetch-instagram`.

Likely viva questions:
- Why are there multiple extraction strategies (JSON, metadata, rendered HTML)?
- Why might post counts come from several possible sources?
- What is the purpose of `warnings` in the profile object?

### [templates/index.html](templates/index.html)
Responsibility: Dashboard markup and form structure.

Key UI sections:
- username input + fetch button
- manual profile form
- result cards and verdict area
- loading spinner and error messages

Interaction:
- JavaScript in `static/app.js` connects to form elements and updates them.

### [static/app.js](static/app.js)
Responsibility: Client-side interaction logic.

Key behaviors:
- validates username format
- calls `/api/fetch-instagram`
- populates form values after successful fetch
- calls `/api/analyze`
- displays prediction, confidence, and verdict
- prevents stale results from staying on screen

Interaction:
- Communicates with the Flask backend.

Likely viva questions:
- Why is it important to clear previous data before fetch?
- How does the UI prevent XSS-like behavior when inserting text?
- Why is the result shown with `textContent` instead of `innerHTML` in critical places?

### [data/instagram_dataset.csv](data/instagram_dataset.csv)
Responsibility: Training dataset used for the classifier.

This file stores the raw dataset used by `model.py`. The model checks for standardized columns like:
- `followers_count`
- `following_count`
- `media_count`
- `has_profile_pic`
- `bio_length`
- `username_length`
- `digit_count_in_username`
- `label`

### [model/account_model.pkl](model/account_model.pkl)
Responsibility: Serialized trained model artifact.

This file is created by `model.py` and used by `app.py` to avoid retraining during each request.

### [model/metrics.json](model/metrics.json)
Responsibility: Evaluation metrics.

The README shows metrics:
- Accuracy: 0.9707
- Precision: 0.9714
- Recall: 0.8500
- F1: 0.9067

## 5. Important code snippets

### Snippet 1: Application entry point and startup model load
File: [app.py](app.py)

```python
MODEL_PATH = BASE_DIR / "model" / "account_model.pkl"

try:
    data = joblib.load(MODEL_PATH)
    MODEL = data["model"]
    FEATURE_COLUMNS = data["feature_columns"]
except Exception as e:
    print(f"Error loading model: {e}")
    MODEL = None
    FEATURE_COLUMNS = []
```

Explanation:
- `BASE_DIR` resolves the project root.
- `joblib.load()` loads the previously trained model.
- `data["model"]` gives the trained classifier object.
- `data["feature_columns"]` stores the exact order needed for consistent prediction.
- If loading fails, the app continues but model inference is unavailable.

Concepts:
- serialization, model artifact, fallback error handling.

Why this implementation:
- Saves training time and speeds prediction.
- Keeps model inputs consistent.

Likely viva questions:
- Why is the model loaded once instead of every request?
- What happens if the file is missing?
- Why is feature order important?

### Snippet 2: Feature extraction logic
File: [utils/features.py](utils/features.py)

```python
def extract_features(
    *,
    username: str,
    bio: str,
    followers_count: int,
    following_count: int,
    media_count: int,
    has_profile_pic: int,
) -> Dict[str, float]:
    cleaned_username = (username or "").strip()
    cleaned_bio = (bio or "").strip()

    username_length = len(cleaned_username)
    digit_count = sum(char.isdigit() for char in cleaned_username)
    bio_length = len(cleaned_bio)
    ratio = float(followers_count) / (float(following_count) + 1.0)
```

Explanation:
- The app strips whitespace from username and bio.
- It counts username characters and digits.
- It calculates profile bio length.
- It computes follower/following ratio to capture suspicious account behavioral imbalance.

Concepts:
- input cleaning, numeric feature engineering, ratio-based heuristics.

Why this implementation:
- Many fake accounts have unusual usernames and incomplete/low-quality profiles.
- These features are cheap to compute and easy to explain.

Likely viva questions:
- Why is the denominator `following_count + 1.0` used?
- Why is bio length relevant?
- What if the following count is zero?

### Snippet 3: Training pipeline
File: [model.py](model.py)

```python
pipeline = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced",
            ),
        ),
    ]
)

pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)
```

Explanation:
- `SimpleImputer` fills missing values with median values.
- `RandomForestClassifier` is the actual model.
- `class_weight='balanced'` helps handle class imbalance.
- `train_test_split` ensures the model is evaluated on unseen data.

Concepts:
- model pipeline, preprocessing, class balancing, holdout evaluation.

Why this implementation:
- Real and fake samples are often imbalanced.
- A pipeline reduces repetition and keeps training consistent.

Likely viva questions:
- Why is a Random Forest chosen instead of a neural network?
- Why is median imputation preferred here?
- Why is `random_state=42` used?

### Snippet 4: Verdict logic
File: [utils/verdict.py](utils/verdict.py)

```python
def compute_verdict(account_prediction: str, account_confidence: float) -> VerdictResult:
    confidence = min(1.0, max(0.0, float(account_confidence)))
    normalized_prediction = account_prediction.strip().lower()
    base_risk = int(round((confidence if normalized_prediction == "fake" else (1.0 - confidence)) * 100))
```

Explanation:
- It normalizes prediction text to lowercase.
- It clamps confidence between 0 and 1.
- It converts the model confidence into a 0–100 risk scale.

Concepts:
- normalization, risk mapping, threshold logic.

Why this implementation:
- Raw model confidence is not always user-friendly.
- The verdict layer makes the output explainable and more presentation-friendly.

Likely viva questions:
- Why is a separate verdict layer useful?
- What is the difference between confidence and risk score?
- Why do fake and real predictions get different treatment?

## 6. Architecture and data flow

### High-level architecture

```mermaid
graph LR
A[User Browser] --> B[Flask Frontend / app.py]
B --> C[/]
B --> D[/api/fetch-instagram]
B --> E[/api/analyze]
D --> F[Instagram profile fetcher]
F --> G[BeautifulSoup + Playwright parsing]
E --> H[Feature extraction]
H --> I[Random Forest model]
I --> J[Prediction + confidence]
J --> K[Verdict engine]
K --> L[JSON response]
L --> A
```

### Step-by-step flow
1. User opens the app in the browser.
2. User enters username or profile data manually.
3. If fetch is requested, `fetch_instagram_profile()` uses Playwright to load the Instagram page.
4. The parser searches nested JSON, OG metadata, and rendered HTML to gather profile values.
5. The backend receives either fetched or manually entered values.
6. `extract_features()` converts them into model inputs.
7. The saved `RandomForestClassifier` predicts Fake or Real.
8. `compute_verdict()` converts that result into a verdict and risk score.
9. The app sends JSON back to the frontend for display.

### Frontend, backend, and model responsibilities
- Frontend: `templates/index.html` + `static/app.js`
- Backend: `app.py`
- Feature engineering: `utils/features.py`
- Model training: `model.py`
- Data fetch layer: `utils/instagram_fetch.py`
- Verdict layer: `utils/verdict.py`

### Important feature tracing

#### Feature 1: Fetch profile and auto-fill fields
- Browser button click calls `fetchInstagram()` in `static/app.js`.
- It sends a POST request to `/api/fetch-instagram`.
- `app.py` calls `fetch_instagram_profile()`.
- The utility inspects HTML and JSON and returns `InstagramProfile`.
- The dashboard fills in bio, followers, following, posts, and has_profile_pic.

#### Feature 2: Analyze account and decide verdict
- User submits form data.
- `analyzeAccount()` sends JSON to `/api/analyze`.
- `app.py` calls `extract_features()`.
- The model predicts `Fake` or `Real` using `MODEL.predict_proba([vector])`.
- `compute_verdict()` returns `verdict`, `risk_score`, and `reasoning`.
- The UI updates the result card.

## 7. Database and data management

### Database type
The project does not use a database such as PostgreSQL, MySQL, SQLite, MongoDB, or a SQLAlchemy model layer. There is no ORM or query layer in the repository.

### How the project stores data
- Training data is stored in CSV files inside `data/` and `csv/`.
- The trained ML pipeline is saved as a serialized pickle-like artifact in `model/account_model.pkl`.
- Runtime profile data is kept in memory as Python dictionaries and dataclass objects.
- API responses are returned as JSON.

### Data flow and persistence model
The system is best described as a file-based ML application rather than a database-driven app.

### Data management considerations
- Input data is validated by the form and API route assumptions.
- Feature extraction converts the values into numeric floats.
- Model artifact ensures reproducibility.
- No backup or migration strategy is present because there is no database.

## 8. Algorithms and technical concepts

### Random Forest Classifier
- Definition: A collection of decision trees combined by voting.
- Why required: It handles tabular profile features well and is easier to interpret than deep learning for a small dataset.
- Where implemented: `model.py`.
- Example: `RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")`.
- Advantages: Good accuracy on tabular data, handles mixed features, robust to noise.
- Limitations: Hard to explain every internal tree; may be biased by sampling or dataset features.

### Feature engineering
- Definition: Turning raw profile metadata into informative model inputs.
- Why required: Model needs numeric values with predictive power.
- Example features: `followers_following_ratio`, `bio_length`, `digit_count_in_username`.
- Where implemented: `model.py`, `utils/features.py`.

### Input validation and normalization
- Definition: Converting and checking user-provided values before processing.
- Why required: Prevents invalid values from breaking the model.
- Where implemented: `app.py`, `utils/features.py`, and parser code.

### HTML/JSON extraction and parsing
- Definition: Searching page source for profile fields in multiple formats.
- Why required: Instagram data can appear in JSON, metadata, or rendered markup.
- Where implemented: `utils/instagram_fetch.py`.
- Advantages: More tolerant to format changes.
- Limitations: Live scraping can fail due to anti-bot changes.

### Rule-based verdict mapping
- Definition: Converting model confidence into human-readable risk labels.
- Why required: Users need a simpler explanation than raw probability.
- Where implemented: `utils/verdict.py`.

## 9. Installation, execution, and demonstration guide

### Prerequisites
- Python 3.14+
- `uv` (recommended) or `pip`
- Browser support for Playwright

### Dependencies
From `pyproject.toml`:
- Flask
- BeautifulSoup4
- joblib
- numpy
- pandas
- scikit-learn
- Playwright
- requests

### Setup commands
Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
uv sync
python -m playwright install
```

Linux/macOS:
```bash
python -m venv .venv
source .venv/bin/activate
uv sync
python -m playwright install
```

### Training the model
```bash
python model.py
```
This creates:
- `model/account_model.pkl`
- `model/metrics.json`

### Running the app
```bash
python app.py
```
Then visit:
```text
http://127.0.0.1:5000
```

### Best order to demonstrate
1. Start the app.
2. Show the home page.
3. Enter a username and click “Fetch Data”.
4. Observe populated fields.
5. Click “Analyze Account”.
6. Show prediction, confidence, verdict, and reasoning.
7. Explain the ML feature logic and model output.

### Expected outputs
- `health` endpoint returns status `ok`.
- Result card contains account status, risk score, verdict, and confidence.
- Warning messages appear if data fetch fails.

### Common errors and troubleshooting
- Model file missing: retrain with `python model.py`.
- Playwright failure: run `python -m playwright install`.
- Wrong Python environment: activate the project virtual environment.
- Missing or stale output: restart Flask because `debug=False` is used in `app.py`.

## 10. Testing and quality assurance

This project includes actual tests in the `tests/` folder.

### Current tests
- `tests/test_instagram_fetch.py`: checks extraction logic for nested JSON, OG metadata, rendered DOM, duplicate links, zero-count handling, and bio parsing.
- `tests/test_profile_ui.cjs`: frontend smoke test for the profile-fetching UI and stale-result handling.

### Verified commands from project summary
```powershell
uv run python -m unittest discover -s tests -p "test*.py"
uv run python -m py_compile utils/instagram_fetch.py tests/test_instagram_fetch.py
node tests/test_profile_ui.cjs
node --check static/app.js
git diff --check
```

### What exists and what is missing
What exists:
- parser unit tests
- frontend smoke test
- model training and metrics generation

What should be added:
- integration test for `/api/analyze`
- model test for fake/real classification boundary
- negative tests for invalid usernames and missing model file
- end-to-end test for running Flask app with sample input

## 11. Strengths of the project

- Clear separation between frontend, backend, model, and utilities
- Real ML pipeline with saved model artifact
- Good use of feature engineering and evaluation metrics
- Live profile-fetch feature adds practical value
- UI is clean and demo-friendly
- Unit tests cover the parser logic

## 12. Limitations and honest assessment

- No user authentication or authorization
- No database layer or persistent storage
- Uses browser-based scraping, which can fail depending on Instagram anti-bot rules
- Model is based on account metadata only; it does not inspect behavior over time
- Risk results are advisory, not final evidence

## 13. Short viva-ready summary

This project demonstrates a full machine learning workflow in a web application. It fetches Instagram profile metadata, engineers features such as follower/following ratio and username length, trains a Random Forest classifier, and shows a risk verdict to the user. It is easy to understand, practical to demonstrate, and suitable for a final-year or project-viva presentation. The project is a strong example of applying Python, Flask, ML, and browser automation together, while also showing important limits such as scraping fragility and the fact that it is not a definitive identity verification system.

## 14. Likely examiner questions and short answers

### Q1: What is the main purpose of this project?
A: To detect whether an Instagram account looks fake or real using machine-learning-based profile analysis.

### Q2: Why is a Random Forest used?
A: It performs well on tabular data and is relatively easy to explain and train in a small project.

### Q3: What is the role of `utils/features.py`?
A: It transforms user input into the numeric features needed by the model.

### Q4: Why is the model loaded only once in `app.py`?
A: To save time and keep prediction consistent without retraining on every request.

### Q5: What are the limitations of the scraping approach?
A: Private accounts, anti-bot protections, rate limits, and page-layout changes can cause fetch failures.

### Q6: Does the project use a database?
A: No. It relies on CSV training data and serialized model files, with runtime state in memory.

### Q7: Is the output definitive?
A: No. It is a screening aid and should not be treated as proof of identity or authenticity.

## 15. Final recommendation for viva delivery

During the viva, speak clearly in layers:
1. Explain the problem and purpose.
2. Explain the architecture simply.
3. Explain the model and its features.
4. Explain the UI workflow.
5. State the limitations honestly.

This makes the project feel structured, realistic, and technically sound.
