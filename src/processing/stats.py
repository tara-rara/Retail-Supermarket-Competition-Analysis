import pandas as pd
import numpy as np
import json
import os
import logging
from scipy import stats

class PriceAnalyzer:
    def __init__(self, log_name="PriceAnalyzer"):
        self.logger = logging.getLogger(log_name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def load_gold_layer(self, gold_path):
        """Load the gold layer into a flat pandas DataFrame for analysis."""
        if not os.path.exists(gold_path):
            self.logger.error(f"Gold layer file {gold_path} not found.")
            return None
        
        records = []
        with open(gold_path, 'r', encoding='utf-8') as f:
            for line in f:
                product = json.loads(line)
                for offer in product['offers']:
                    records.append({
                        'product_id': product['product_id'],
                        'title': product['title'],
                        'brand': product['brand'],
                        'quantity': product['quantity'],
                        'unit': product['unit'],
                        'category': product['category'],
                        'store': offer['store'],
                        'city': offer['city'],
                        'price': offer['price'],
                        'unit_price': offer['unit_price']
                    })
        
        df = pd.DataFrame(records)
        self.logger.info(f"Loaded {len(df)} records for analysis.")
        return df

    def calculate_price_dispersion(self, df):
        """Phase 5.1: Calculate per-product dispersion metrics (Mandatory)."""
        # Group by product and calculate stats
        agg_funcs = {
            'price': ['mean', 'median', 'std', 'min', 'max', lambda x: x.quantile(0.75) - x.quantile(0.25)]
        }
        
        product_stats = df.groupby('product_id').agg(agg_funcs).reset_index()
        product_stats.columns = ['product_id', 'mean', 'median', 'std', 'min', 'max', 'iqr']
        
        # Handle cases with only 1 price (std will be NaN/0)
        product_stats['std'] = product_stats['std'].fillna(0)
        
        # 5.1 Mandatory Calculations
        product_stats['cv'] = (product_stats['std'] / product_stats['mean']).fillna(0)
        product_stats['price_range'] = product_stats['max'] - product_stats['min']
        # MANDATORY: Price Spread Ratio (max / min)
        product_stats['price_spread_ratio'] = (product_stats['max'] / product_stats['min']).replace([np.inf, -np.inf], 1.0)
        
        return product_stats

    def calculate_relative_position(self, df):
        """Phase 5.1: Relative Price Position Index: store_price / category_mean."""
        # Calculate category means per city
        cat_means = df.groupby(['city', 'category'])['price'].mean().reset_index()
        cat_means.rename(columns={'price': 'category_mean'}, inplace=True)
        
        # Merge back to original df
        df_merged = df.merge(cat_means, on=['city', 'category'], how='left')
        
        # MANDATORY: store_price / category_mean
        # (Lower means store is cheaper than average)
        df_merged['relative_price_position'] = df_merged['price'] / df_merged['category_mean']
        
        return df_merged

    def calculate_store_metrics(self, df_with_relative):
        """Phase 5.2 & 5.3: Store-Level, Market Dominance and LDI."""
        # Group by store and city
        store_metrics = df_with_relative.groupby(['store', 'city']).agg({
            'relative_price_position': 'mean',
            'price': 'std' # Basic volatility
        }).reset_index()
        
        # Median Price Deviation
        median_dev = df_with_relative.groupby(['store', 'city']).apply(
            lambda x: (x['price'] - x['price'].median()).abs().median(), include_groups=False
        ).reset_index(name='median_price_deviation')
        
        store_metrics = store_metrics.merge(median_dev, on=['store', 'city'])
        store_metrics.rename(columns={
            'relative_price_position': 'avg_category_price_index',
            'price': 'price_volatility_score'
        }, inplace=True)
        
        # LDI Calculation
        min_prices = df_with_relative.groupby('product_id')['price'].transform('min')
        df_with_relative['is_lowest'] = df_with_relative['price'] == min_prices
        
        total_unique_products = df_with_relative['product_id'].nunique()
        
        # Category size for weighting
        cat_sizes = df_with_relative.groupby('category').size().reset_index(name='cat_size')
        df_with_relative = df_with_relative.merge(cat_sizes, on='category')
        
        ldi_records = []
        for (store, city), group in df_with_relative.groupby(['store', 'city']):
            wins = group['is_lowest'].sum()
            
            # MANDATORY: LDI Formula = Wins / Total matched products
            ldi = wins / total_unique_products if total_unique_products > 0 else 0
            
            # 3.3 Weighted LDI (Weighted by category size)
            weighted_wins = group[group['is_lowest']]['cat_size'].sum()
            total_weight = cat_sizes['cat_size'].sum()
            weighted_ldi = weighted_wins / total_weight if total_weight > 0 else 0
            
            # 3.2 Price Leadership Frequency
            leadership_freq = wins / len(group) if len(group) > 0 else 0
            
            ldi_records.append({
                'store': store, 'city': city, 
                'ldi': ldi, 
                'weighted_ldi': weighted_ldi,
                'leadership_frequency': leadership_freq,
                'wins': wins
            })
            
        ldi_df = pd.DataFrame(ldi_records)
        store_metrics = store_metrics.merge(ldi_df, on=['store', 'city'])
        
        # 3.3 Category-wise LDI
        cat_ldi = df_with_relative.groupby(['category', 'store']).apply(
            lambda x: x['is_lowest'].sum() / x['product_id'].nunique(), include_groups=False
        ).reset_index(name='cat_ldi')
        
        return store_metrics, cat_ldi

    def run_correlations(self, df, product_stats):
        """Phase 5.3 & 5.4: Mandatory Correlation Tasks."""
        product_info = df.drop_duplicates(subset=['product_id'])[['product_id', 'quantity', 'brand', 'category', 'city']]
        merged = product_stats.merge(product_info, on='product_id')
        
        # 1. Product size vs price dispersion
        size_disp_corr = merged[['quantity', 'cv']].corr().iloc[0, 1]
        
        # 2. Number of competitors vs price spread
        competitors = df.groupby('product_id').size().reset_index(name='competitor_count')
        merged = merged.merge(competitors, on='product_id')
        comp_spread_corr = merged[['competitor_count', 'price_spread_ratio']].corr().iloc[0, 1]
        
        # 3. Brand Tier vs Volatility
        cat_medians = df.groupby('category')['unit_price'].median().reset_index()
        cat_medians.rename(columns={'unit_price': 'cat_median_unit_price'}, inplace=True)
        df_brand = df.merge(cat_medians, on='category')
        brand_means = df_brand.groupby(['brand', 'category']).agg({'unit_price': 'mean', 'cat_median_unit_price': 'first'}).reset_index()
        brand_means['is_premium'] = brand_means['unit_price'] > (brand_means['cat_median_unit_price'] * 1.5)
        
        brand_vols = df.groupby(['brand', 'category'])['unit_price'].std().reset_index().rename(columns={'unit_price': 'volatility'})
        brand_analysis = brand_means.merge(brand_vols, on=['brand', 'category'])
        brand_tier_corr = brand_analysis[['is_premium', 'volatility']].corr().iloc[0, 1]
        
        # 5.4 Cross-store price synchronization score (Correlation of matched prices)
        sync_score = 0
        # Group by product and store to handle multiple cities
        pivot_data = df.groupby(['product_id', 'store'])['price'].mean().reset_index()
        pivot_df = pivot_data.pivot(index='product_id', columns='store', values='price').dropna(thresh=2)
        if not pivot_df.empty:
            sync_score = pivot_df.corr().mean().mean()
            
        # 4. City-wise Correlation Matrix
        city_corrs = {}
        for city in df['city'].unique():
            city_df = merged[merged['city'] == city]
            if not city_df.empty:
                numeric_df = city_df.select_dtypes(include=[np.number])
                city_corrs[city] = numeric_df.corr(method='pearson')
                
        return {
            'size_vs_dispersion': size_disp_corr,
            'competitors_vs_spread': comp_spread_corr,
            'brand_tier_vs_volatility': brand_tier_corr,
            'synchronization_score': sync_score,
            'city_correlations': city_corrs
        }
