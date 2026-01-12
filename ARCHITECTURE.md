# 🏗️ Architecture & Design Document

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│                                                                   │
│  ┌──────────────┐              ┌──────────────────┐             │
│  │  PDF Upload  │              │  Web Scraper     │             │
│  │              │              │  (SEC EDGAR)     │             │
│  └──────┬───────┘              └────────┬─────────┘             │
│         │                               │                        │
└─────────┼───────────────────────────────┼────────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────┐
│                    PROCESSING LAYER                               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              PDF Parser & OCR Engine                      │   │
│  │  • pdfplumber (digital PDFs)                             │   │
│  │  • pytesseract (OCR for scans)                           │   │
│  │  • camelot/tabula (table extraction)                     │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │         Financial Statement Extractor                    │   │
│  │  • NLP-based line item recognition                       │   │
│  │  • Table structure analysis                              │   │
│  │  • Multi-period data extraction                          │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │         GAAP/IFRS Classifier                             │   │
│  │  • Keyword detection                                     │   │
│  │  • Policy analysis                                       │   │
│  │  • Statement structure recognition                       │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    MODELING LAYER                                 │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Financial Model Engine                           │   │
│  │                                                          │   │
│  │  Linkages:                                               │   │
│  │  • Net Income → Retained Earnings                        │   │
│  │  • Cash Flow → Cash Balance                              │   │
│  │  • CAPEX & D&A → PPE                                     │   │
│  │  • Working Capital → Operating CF                        │   │
│  │                                                          │   │
│  │  Validation:                                             │   │
│  │  • Assets = Liabilities + Equity                         │   │
│  │  • Cash reconciliation                                   │   │
│  │  • Period-over-period consistency                        │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐   │
│  │         Forecast Engine                                  │   │
│  │                                                          │   │
│  │  Driver-Based Forecasting:                               │   │
│  │  • Revenue growth assumptions                            │   │
│  │  • Margin targets                                        │   │
│  │  • Working capital days                                  │   │
│  │  • CAPEX % of revenue                                    │   │
│  │                                                          │   │
│  │  Scenarios:                                              │   │
│  │  • Base case                                             │   │
│  │  • Bull case (optimistic)                                │   │
│  │  • Bear case (pessimistic)                               │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    OUTPUT LAYER                                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Report Generator                                 │   │
│  │                                                          │   │
│  │  Components:                                             │   │
│  │  • Executive summary                                     │   │
│  │  • Historical financials (tables)                        │   │
│  │  • Linked model explanation                              │   │
│  │  • Forecast projections                                  │   │
│  │  • Financial ratios & KPIs                               │   │
│  │  • Charts & visualizations                               │   │
│  │  • GAAP/IFRS adjustments                                 │   │
│  │  • Commentary & insights                                 │   │
│  │                                                          │   │
│  │  Output: Professional PDF Report                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Input Processing
```
PDF File → PDF Parser → Raw Text + Tables
                    ↓
              Text Analysis
                    ↓
         GAAP/IFRS Classification
```

### 2. Data Extraction
```
Raw Tables → Table Classifier → Statement Type Detection
                              ↓
                    Line Item Extraction
                              ↓
                    Structured Data (JSON)
```

### 3. Model Building
```
Structured Data → Validation → Historical Model
                             ↓
                    Linkage Validation
                             ↓
                    Linked 3-Statement Model
```

### 4. Forecasting
```
Historical Model → Assumptions → Driver Calculation
                              ↓
                    Period-by-Period Forecast
                              ↓
                    Forecast Validation
```

### 5. Report Generation
```
Complete Model → Template Engine → PDF Components
                                 ↓
                        Chart Generation
                                 ↓
                        Final PDF Report
```

## Core Algorithms

### 1. Statement Linking Algorithm

```python
def link_statements(income, balance_sheet_prev, balance_sheet_curr, cash_flow):
    """
    Link 1: Net Income → Retained Earnings
    """
    expected_RE = (
        balance_sheet_prev.retained_earnings +
        income.net_income -
        cash_flow.dividends_paid
    )
    assert abs(expected_RE - balance_sheet_curr.retained_earnings) < TOLERANCE
    
    """
    Link 2: Cash Flow → Cash Balance
    """
    expected_cash = (
        balance_sheet_prev.cash +
        cash_flow.cash_from_operations +
        cash_flow.cash_from_investing +
        cash_flow.cash_from_financing
    )
    assert abs(expected_cash - balance_sheet_curr.cash) < TOLERANCE
    
    """
    Link 3: CAPEX & D&A → PPE
    """
    expected_ppe = (
        balance_sheet_prev.ppe_net +
        abs(cash_flow.capex) -
        income.depreciation_amortization
    )
    # Note: May have variance due to acquisitions/disposals
    
    """
    Link 4: Balance Sheet Balance
    """
    assert abs(
        balance_sheet_curr.total_assets -
        (balance_sheet_curr.total_liabilities + 
         balance_sheet_curr.total_equity)
    ) < TOLERANCE
```

### 2. Forecasting Algorithm

```python
def forecast_period(prev_income, prev_bs, assumptions):
    """
    Revenue-driven forecasting
    """
    # 1. Revenue (key driver)
    revenue = prev_income.revenue * (1 + assumptions.growth_rate)
    
    # 2. Income Statement (margin-driven)
    gross_profit = revenue * assumptions.gross_margin
    operating_income = revenue * assumptions.operating_margin
    net_income = operating_income * (1 - assumptions.tax_rate)
    
    # 3. Balance Sheet (working capital days)
    accounts_receivable = (revenue / 365) * assumptions.dso
    inventory = (cogs / 365) * assumptions.dio
    accounts_payable = (cogs / 365) * assumptions.dpo
    
    # 4. PPE (CAPEX-driven)
    capex = revenue * assumptions.capex_pct
    ppe = prev_bs.ppe + capex - depreciation
    
    # 5. Retained Earnings (linking)
    retained_earnings = prev_bs.retained_earnings + net_income - dividends
    
    # 6. Cash (plug to balance)
    cash = calculate_plug_to_balance()
    
    # 7. Cash Flow (derived)
    cash_from_ops = net_income + depreciation + wc_changes
    cash_from_investing = -capex
    cash_from_financing = dividends + debt_changes
    
    return forecast_statements
```

### 3. GAAP vs IFRS Detection Algorithm

```python
def classify_standard(text):
    """
    Multi-method classification with scoring
    """
    gaap_score = 0
    ifrs_score = 0
    
    # Method 1: Explicit mentions
    gaap_score += count_keywords(text, GAAP_KEYWORDS) * 2
    ifrs_score += count_keywords(text, IFRS_KEYWORDS) * 2
    
    # Method 2: Statement names
    if "statement of operations" in text:
        gaap_score += 5
    if "statement of comprehensive income" in text:
        ifrs_score += 5
    
    # Method 3: Accounting policies
    if "lifo" in text:
        gaap_score += 4
    if "revaluation model" in text:
        ifrs_score += 4
    
    # Method 4: Regulatory references
    gaap_score += count_keywords(text, ["sec", "fasb", "asc"]) * 1.5
    ifrs_score += count_keywords(text, ["iasb", "ias", "ifrs"]) * 1.5
    
    # Determine winner
    if gaap_score > ifrs_score and gaap_score > THRESHOLD:
        return "GAAP", confidence(gaap_score, ifrs_score)
    elif ifrs_score > gaap_score and ifrs_score > THRESHOLD:
        return "IFRS", confidence(ifrs_score, gaap_score)
    else:
        return "UNKNOWN", 0.0
```

## Data Models

### Financial Statements Schema

```json
{
  "company_name": "Apple Inc.",
  "ticker": "AAPL",
  "fiscal_year": 2023,
  "report_type": "10-K",
  "accounting_standard": "GAAP",
  "currency": "USD",
  
  "income_statements": [
    {
      "period_start": "2023-01-01",
      "period_end": "2023-12-31",
      "revenue": 383285000000,
      "cost_of_revenue": 214137000000,
      "gross_profit": 169148000000,
      "operating_expenses": 54780000000,
      "operating_income": 114368000000,
      "net_income": 96995000000
    }
  ],
  
  "balance_sheets": [
    {
      "period_end": "2023-12-31",
      "cash_and_equivalents": 29965000000,
      "total_current_assets": 143566000000,
      "total_assets": 352755000000,
      "total_current_liabilities": 133973000000,
      "total_liabilities": 290437000000,
      "total_shareholders_equity": 62318000000
    }
  ],
  
  "cash_flow_statements": [
    {
      "period_start": "2023-01-01",
      "period_end": "2023-12-31",
      "cash_from_operations": 110543000000,
      "capital_expenditures": -10959000000,
      "cash_from_investing": -3705000000,
      "dividends_paid": -14841000000,
      "cash_from_financing": -106488000000
    }
  ]
}
```

## Technology Stack Details

### PDF Processing
- **pdfplumber**: Primary digital PDF text extraction
- **PyPDF2**: Metadata extraction
- **pytesseract**: OCR for scanned documents
- **pdf2image**: PDF to image conversion for OCR
- **camelot-py**: Advanced table extraction (lattice method)
- **tabula-py**: Alternative table extraction (stream method)

### Data Processing
- **pandas**: DataFrame operations, data manipulation
- **numpy**: Numerical computations
- **openpyxl**: Excel file support

### NLP & AI (Future Enhancement)
- **transformers**: BERT/GPT models for intelligent extraction
- **spacy**: Named entity recognition
- **openai**: GPT-4 API for insights generation

### Visualization
- **matplotlib**: Static charts
- **plotly**: Interactive visualizations
- **seaborn**: Statistical graphics

### PDF Generation
- **reportlab**: PDF creation and layout
- **weasyprint**: HTML to PDF conversion
- **jinja2**: Template engine

### API Framework
- **FastAPI**: REST API
- **uvicorn**: ASGI server
- **pydantic**: Data validation

## Scaling to SaaS

### Phase 1: MVP (Current)
- Desktop application
- PDF upload
- Single-user processing
- Local file storage

### Phase 2: Web Application
```
Frontend: React/Vue.js
Backend: FastAPI
Database: PostgreSQL
Storage: AWS S3
Queue: Celery + Redis
```

### Phase 3: Multi-tenant SaaS
```
Features:
- User authentication (Auth0/Cognito)
- Company workspaces
- Collaborative features
- API access
- Webhook integrations
- Real-time data feeds
```

### Phase 4: Enterprise
```
Features:
- SSO integration
- Custom templates
- White-labeling
- On-premise deployment
- Advanced analytics
- ML-powered insights
```

## Performance Considerations

### Optimization Strategies
1. **Async Processing**: Use Celery for long-running tasks
2. **Caching**: Redis for frequently accessed data
3. **Batch Processing**: Process multiple reports in parallel
4. **Database Indexing**: Optimize queries for large datasets
5. **CDN**: Serve static assets and reports via CDN

### Scalability Metrics
- **Processing Speed**: 1 report in 30-60 seconds
- **Concurrent Users**: 100+ simultaneous analyses
- **Storage**: Efficient compression for historical data
- **API Rate Limits**: 1000 requests/hour per user

## Security

### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Secure file upload validation
- Input sanitization
- SQL injection prevention

### Access Control
- Role-based access control (RBAC)
- Multi-factor authentication
- Audit logging
- Session management

## Testing Strategy

### Unit Tests
- Individual module testing
- Mock data for PDF parsing
- Validation logic testing

### Integration Tests
- End-to-end pipeline testing
- Database integration
- API endpoint testing

### Performance Tests
- Load testing (100+ concurrent users)
- Stress testing
- Memory profiling

## Deployment

### Development
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Deployment
- **AWS**: ECS/Fargate + RDS + S3
- **GCP**: Cloud Run + Cloud SQL + Cloud Storage
- **Azure**: App Service + Azure SQL + Blob Storage
