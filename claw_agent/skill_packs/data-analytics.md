# Data & Analytics Skill Pack

## Data Engineering
- **ETL/ELT**: Extract first, transform in the warehouse. dbt for transformations
- **Schema design**: Star schema for analytics. Snowflake schema when dimensions are complex
- **Data quality**: Validate at ingestion. Null checks, type checks, range checks, uniqueness
- **Incremental processing**: Process only new/changed data. Watermarks or CDC (Change Data Capture)
- **Idempotency**: Every pipeline step can be safely re-run without duplicating data

## SQL Mastery
- Window functions: `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`, `SUM() OVER()`
- CTEs over nested subqueries — readable, debuggable, maintainable
- `EXPLAIN ANALYZE` before optimizing. Index the right columns
- Avoid `SELECT *` in production queries. Name columns explicitly
- Date/time: Always store UTC. Convert to local on display

## Python Data Stack
- **Pandas**: `df.pipe()` for chainable transforms. Avoid iterrows — use vectorized ops
- **Polars**: For large datasets. Lazy evaluation, faster than pandas
- **NumPy**: Vectorized operations. Broadcast rules. Avoid Python loops over arrays
- **Visualization**: Matplotlib for publication, Plotly for interactive, Seaborn for statistical

## Machine Learning Pipeline
- Split data first: train/validation/test. No data leakage from test into training
- Feature engineering: Domain knowledge beats algorithmic tricks
- Cross-validation: k-fold for small datasets, hold-out for large
- Metrics: Accuracy is misleading for imbalanced data. Use precision/recall/F1/AUC
- Model registry: Track versions, parameters, metrics. MLflow or equivalent

## Analytics & BI
- Event tracking: Define taxonomy before implementing. Consistent naming
- Funnel analysis: Identify where users drop off. Segment by cohort
- Cohort analysis: Group users by signup date/event. Track retention over time
- A/B testing: Define hypothesis, calculate sample size, run to completion, check significance
- GA4/Mixpanel/Amplitude: Use server-side tracking for reliability
