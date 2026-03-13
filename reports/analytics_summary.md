# 🛡️ CS4048: Supermarket Pricing Intelligence Report

## 1. Market Infrastructure Overview
- **Total Scraped Rows (Raw):** 14482 (Goal: 500k+ in full run)
- **Golden Entities (Matched):** 8633 (Goal: 10,000+)
- **Unique Market Brands:** 911
- **Cross-Store Price Sync Score:** 0.0000

## 2. Store-Level Dominance & LDI (Mandatory Task 3.2 & 3.3)
| store   | city       |   avg_category_price_index |        ldi |   weighted_ldi |   leadership_frequency |   median_price_deviation |
|:--------|:-----------|---------------------------:|-----------:|---------------:|-----------------------:|-------------------------:|
| AlFatah | Faisalabad |                          1 | 0.81478    |   1530.74      |               0.999716 |                   1750   |
| AlFatah | Lahore     |                          1 | 0.841075   |   1505.88      |               0.998899 |                   1320   |
| Imtiaz  | Islamabad  |                          1 | 0.00428588 |      0.0366662 |               1        |                    130   |
| Imtiaz  | Karachi    |                          1 | 0.00463338 |      0.0305206 |               1        |                     92.5 |
| Metro   | Karachi    |                          1 | 0.00474922 |      0.28311   |               0.87234  |                    111   |
| Metro   | Lahore     |                          1 | 0.00613923 |      0.365972  |               1        |                    111   |

*LDI = Wins / Total Matched. Leadership Freq = Wins / Store Total.*

## 3. Mandatory Correlation Analysis (Task 3.4)
| Correlation Task | Pearson Coefficient |
| :--- | :--- |
| Product Size vs Price Dispersion (CV) | -0.0010 |
| Competitors vs Price Spread Ratio | 0.0217 |
| Brand Tier vs Price Volatility | 0.4122 |


## 4. City-wise Competition Matrix
### Faisalabad Region
|      |         mean |         std |         cv |
|:-----|-------------:|------------:|-----------:|
| mean |  1           | 0.000609686 | -0.0064773 |
| std  |  0.000609686 | 1           |  0.762758  |
| cv   | -0.0064773   | 0.762758    |  1         |

### Lahore Region
|      |   mean |   std |   cv |
|:-----|-------:|------:|-----:|
| mean |      1 |     0 |    0 |
| std  |      0 |     0 |    0 |
| cv   |      0 |     0 |    0 |

### Islamabad Region
|      |   mean |   std |   cv |
|:-----|-------:|------:|-----:|
| mean |      1 |     0 |    0 |
| std  |      0 |     0 |    0 |
| cv   |      0 |     0 |    0 |

### Karachi Region
|      |       mean |        std |         cv |
|:-----|-----------:|-----------:|-----------:|
| mean |  1         | -0.0259123 | -0.0537044 |
| std  | -0.0259123 |  1         |  0.65791   |
| cv   | -0.0537044 |  0.65791   |  1         |

## 5. Top 10 High-Competition Categories (Category LDI)
| category        |   cat_ldi |
|:----------------|----------:|
| Beverages       |   2       |
| Electronics     |   2       |
| Baby-Care       |   1.99844 |
| Perfumes        |   1.99265 |
| Grocery         |   1.70909 |
| Makeup          |   1.5733  |
| Skin-Care       |   1.42236 |
| Flour           |   1       |
| Health & Beauty |   1       |
| Home Care       |   1       |

