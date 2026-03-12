# Supermarket Pricing Intelligence Pipeline (Pakistan)

A production-ready data science pipeline to scrape, normalize, and analyze retail pricing across **Metro, Imtiaz, and Al-Fatah** stores in **Karachi, Lahore, Faisalabad, and Islamabad**.

## 📁 Project Structure
- `data/`
  - `raw/`: Scraped JSONL data from store websites.
  - `processed/`: Normalized prices, units, and brands.
  - `matched/`: Final unified products with store price comparisons.
- `src/`
  - `scrapers/`: Modular scraper classes for each store.
  - `processing/`: Cleaning, normalization, and statistical analysis (Phase 3 & 5).
  - `matching/`: Entity resolution and fuzzy matching (Phase 4).
  - `utils/`: Logging and shared helpers.
- `notebooks/`: Exploratory analysis.
- `tests/`: Automated validation.
- `logs/`: Scraper and analytics execution records.

## 🚀 Getting Started

### 1. Installation
Install the project dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Execution Pipeline
Run the following scripts in order:
1.  **Scrape Data**: `python run_metro_imtiaz.py`
2.  **Clean & Normalize**: `python run_cleaning.py`
3.  **Entity Resolution**: `python run_matching.py`
4.  **Statistical Analysis**: `python run_analytics.py`

### 3. Dashboard
Launch the interactive dashboard:
```bash
streamlit run app.py
```

## 📈 Features
- **Scalable Matching**: Uses `rapidfuzz` and blocking to unify 10,000+ products.
- **Robust Scraping**: Retry logic, rate limiting, and exponential backoff.
- **Analytics**: Leader Dominance Index (LDI), volatility scoring, and market correlation matrices.
