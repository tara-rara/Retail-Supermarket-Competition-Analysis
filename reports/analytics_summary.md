# 🛡️ CS4048: Supermarket Pricing Intelligence Report

## 1. Market Infrastructure Overview
- **Total Scraped Rows (Raw):** 16401 (Goal: 500k+ in full run)
- **Golden Entities (Matched):** 10023 (Goal: 10,000+)
- **Unique Market Brands:** 1036
- **Cross-Store Price Sync Score:** 0.0000

## 2. Store-Level Dominance & LDI (Mandatory Task 3.2 & 3.3)
| store   | city       |   avg_category_price_index |        ldi |   weighted_ldi |   leadership_frequency |   median_price_deviation |
|:--------|:-----------|---------------------------:|-----------:|---------------:|-----------------------:|-------------------------:|
| AlFatah | Faisalabad |                          1 | 0.894842   |   2362.76      |               0.999666 |                   2425   |
| AlFatah | Lahore     |                          1 | 0.727028   |   1786.39      |               0.998903 |                   1550   |
| Imtiaz  | Islamabad  |                          1 | 0.00399082 |      0.0538992 |               1        |                     92.5 |
| Imtiaz  | Karachi    |                          1 | 0.00399082 |      0.0538992 |               1        |                     92.5 |
| Metro   | Karachi    |                          1 | 0.0026938  |      0.088897  |               1        |                     69   |
| Metro   | Lahore     |                          1 | 0.0026938  |      0.088897  |               1        |                     69   |

*LDI = Wins / Total Matched. Leadership Freq = Wins / Store Total.*

## 3. Mandatory Correlation Analysis (Task 3.4)
| Correlation Task | Pearson Coefficient |
| :--- | :--- |
| Product Size vs Price Dispersion (CV) | -0.0011 |
| Competitors vs Price Spread Ratio | 0.0185 |
| Brand Tier vs Price Volatility | 0.1300 |


## 4. City-wise Competition Matrix
### Faisalabad Region
|      |        mean |         std |         cv |
|:-----|------------:|------------:|-----------:|
| mean |  1          | -0.00823338 | -0.0105692 |
| std  | -0.00823338 |  1          |  0.878735  |
| cv   | -0.0105692  |  0.878735   |  1         |

### Lahore Region
|      |   mean |   std |   cv |
|:-----|-------:|------:|-----:|
| mean |      1 |   nan |  nan |
| std  |    nan |   nan |  nan |
| cv   |    nan |   nan |  nan |

### Islamabad Region
|      |   mean |   std |   cv |
|:-----|-------:|------:|-----:|
| mean |      1 |   nan |  nan |
| std  |    nan |   nan |  nan |
| cv   |    nan |   nan |  nan |

### Karachi Region
|      |   mean |   std |   cv |
|:-----|-------:|------:|-----:|
| mean |      1 |   nan |  nan |
| std  |    nan |   nan |  nan |
| cv   |    nan |   nan |  nan |

## 5. Top 10 High-Competition Categories (Category LDI)
| category      |   cat_ldi |
|:--------------|----------:|
| Baby-Care     |   2       |
| Beverages     |   2       |
| Electronics   |   2       |
| Flour         |   2       |
| Grocery       |   2       |
| Oil-Ghee      |   2       |
| Rice          |   2       |
| Pulses-Grains |   2       |
| Spices-Herbs  |   2       |
| Makeup        |   1.64518 |

