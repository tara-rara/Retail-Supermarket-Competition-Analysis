import os
import json
import logging
import pandas as pd
from src.processing.stats import PriceAnalyzer

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/analytics.log"),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("AnalyticsOrchestrator")
    
    gold_path = "data/matched/matched_products.jsonl"
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    
    analyzer = PriceAnalyzer()
    
    # Load Data
    df = analyzer.load_gold_layer(gold_path)
    if df is None or df.empty:
        logger.error("No data loaded. Analytics could not be completed.")
        return
        
    # Phase 5.1: Price Dispersion
    product_stats = analyzer.calculate_price_dispersion(df)
    logger.info(f"Calculated dispersion metrics for {len(product_stats)} unique products.")
    
    # 5.1 & 5.2: Relative Position & Store Aggregates
    df_with_rel = analyzer.calculate_relative_position(df)
    store_metrics, cat_ldi = analyzer.calculate_store_metrics(df_with_rel)
    logger.info("Calculated store-level dominance, volatility, and LDI.")
    
    # Phase 5.3 & 5.4: Correlations & Competition
    corr_res = analyzer.run_correlations(df, product_stats)
    logger.info("Computed correlation and synchronization tasks.")
    
    # Save Outputs
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    product_stats.to_csv(os.path.join(report_dir, "product_dispersion_metrics.csv"), index=False)
    store_metrics.to_csv(os.path.join(report_dir, "store_market_metrics.csv"), index=False)
    cat_ldi.to_csv(os.path.join(report_dir, "category_ldi_stats.csv"), index=False)
    
    # Generate Advanced Summary Report (Markdown)
    with open(os.path.join(report_dir, "analytics_summary.md"), 'w', encoding='utf-8') as f:
        f.write("# 🛡️ CS4048: Supermarket Pricing Intelligence Report\n\n")
        
        f.write("## 1. Market Infrastructure Overview\n")
        f.write(f"- **Total Scraped Rows (Raw):** {len(df)} (Goal: 500k+ in full run)\n")
        f.write(f"- **Golden Entities (Matched):** {len(product_stats)} (Goal: 10,000+)\n")
        f.write(f"- **Unique Market Brands:** {df['brand'].nunique()}\n")
        f.write(f"- **Cross-Store Price Sync Score:** {corr_res['synchronization_score']:.4f}\n\n")
        
        f.write("## 2. Store-Level Dominance & LDI (Mandatory Task 3.2 & 3.3)\n")
        cols = ['store', 'city', 'avg_category_price_index', 'ldi', 'weighted_ldi', 'leadership_frequency', 'median_price_deviation']
        f.write(store_metrics[cols].to_markdown(index=False))
        f.write("\n\n*LDI = Wins / Total Matched. Leadership Freq = Wins / Store Total.*\n\n")
        
        f.write("## 3. Mandatory Correlation Analysis (Task 3.4)\n")
        f.write("| Correlation Task | Pearson Coefficient |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| Product Size vs Price Dispersion (CV) | {corr_res['size_vs_dispersion']:.4f} |\n")
        f.write(f"| Competitors vs Price Spread Ratio | {corr_res['competitors_vs_spread']:.4f} |\n")
        f.write(f"| Brand Tier vs Price Volatility | {corr_res['brand_tier_vs_volatility']:.4f} |\n")
        f.write("\n\n")
        
        f.write("## 4. City-wise Competition Matrix\n")
        for city, mat in corr_res['city_correlations'].items():
            f.write(f"### {city} Region\n")
            subset = mat.loc[['mean', 'std', 'cv'], ['mean', 'std', 'cv']]
            f.write(subset.to_markdown())
            f.write("\n\n")
        
        f.write("## 5. Top 10 High-Competition Categories (Category LDI)\n")
        top_cats = cat_ldi.groupby('category')['cat_ldi'].mean().sort_values(ascending=False).head(10)
        f.write(top_cats.to_markdown())
        f.write("\n\n")

    logger.info(f"Analysis complete. High-fidelity reports generated in {report_dir}/")

    logger.info(f"Analysis complete. Reports available in {report_dir}/")

if __name__ == "__main__":
    main()
