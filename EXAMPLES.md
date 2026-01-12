# 📚 Usage Examples

## Basic Usage

### 1. Analyze a PDF Report

```python
from src.core.pdf_parser import PDFParser
from src.core.model_engine import ModelEngine
from src.core.forecast_engine import ForecastEngine
from src.core.report_generator import ReportGenerator

# Parse PDF
parser = PDFParser("path/to/10k.pdf")
data = parser.extract()

# Extract statements (simplified - use FinancialExtractor in production)
statements = extract_statements(data)

# Build linked model
engine = ModelEngine(statements)
model = engine.build_linked_model()

# Generate forecast
forecast_engine = ForecastEngine(model)
forecast = forecast_engine.forecast(years=5)

# Generate report
generator = ReportGenerator(forecast)
generator.generate_pdf("output/report.pdf")
```

### 2. GAAP vs IFRS Classification

```python
from src.core.gaap_ifrs_classifier import GaapIfrsClassifier

classifier = GaapIfrsClassifier()
standard, confidence, evidence = classifier.classify(text)

print(f"Standard: {standard.value}")
print(f"Confidence: {confidence:.1%}")
print(f"Evidence: {evidence}")
```

### 3. Custom Forecast Assumptions

```python
from src.models.schemas import ForecastAssumptions

assumptions = ForecastAssumptions(
    revenue_growth_rate=0.10,  # 10% growth
    gross_margin=0.45,
    operating_margin=0.25,
    tax_rate=0.21,
    capex_percent_of_revenue=0.08,
    days_sales_outstanding=40,
    days_inventory_outstanding=50,
    days_payable_outstanding=30
)

forecast = forecast_engine.forecast(
    years=5,
    assumptions=assumptions,
    scenario="bull"
)
```

### 4. Scenario Analysis

```python
scenarios = {}

for scenario_name in ['base', 'bull', 'bear']:
    engine = ForecastEngine(linked_model)
    scenarios[scenario_name] = engine.forecast(
        years=5,
        scenario=scenario_name
    )

# Compare scenarios
for name, model in scenarios.items():
    final_revenue = model.forecast_income_statements[-1].revenue
    print(f"{name}: ${final_revenue:,.0f}")
```

## Advanced Usage

### 5. Batch Processing

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def process_report(pdf_path):
    parser = PDFParser(pdf_path)
    data = parser.extract()
    # ... rest of pipeline
    return result

pdf_files = list(Path("data/reports").glob("*.pdf"))

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_report, pdf_files))
```

### 6. Custom Validation Rules

```python
from src.core.model_engine import ModelEngine

class CustomModelEngine(ModelEngine):
    def _validate_linkages(self):
        # Add custom validation logic
        is_valid = super()._validate_linkages()
        
        # Custom check: Revenue growth < 50%
        for i in range(1, len(self.statements.income_statements)):
            prev = self.statements.income_statements[i-1].revenue
            curr = self.statements.income_statements[i].revenue
            growth = (curr - prev) / prev
            
            if growth > 0.5:
                self.validation_errors.append(
                    f"Unusual revenue growth: {growth:.1%}"
                )
                is_valid = False
        
        return is_valid
```

### 7. Export to Excel

```python
import pandas as pd

def export_to_excel(model, output_path):
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Income Statement
        income_data = []
        for stmt in model.historical_income_statements:
            income_data.append({
                'Year': stmt.period_end.year,
                'Revenue': stmt.revenue,
                'Gross Profit': stmt.gross_profit,
                'Operating Income': stmt.operating_income,
                'Net Income': stmt.net_income
            })
        
        df_income = pd.DataFrame(income_data)
        df_income.to_excel(writer, sheet_name='Income Statement', index=False)
        
        # Balance Sheet
        # ... similar for other statements

export_to_excel(linked_model, "output/financials.xlsx")
```

### 8. API Integration

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/analyze")
async def analyze_report(file: UploadFile = File(...)):
    # Save uploaded file
    pdf_path = f"temp/{file.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await file.read())
    
    # Process
    parser = PDFParser(pdf_path)
    data = parser.extract()
    # ... rest of pipeline
    
    # Return report
    return FileResponse(
        "output/report.pdf",
        media_type="application/pdf",
        filename="financial_analysis.pdf"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 9. Database Integration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://user:pass@localhost/financedb')
Session = sessionmaker(bind=engine)

def save_to_database(model):
    session = Session()
    
    try:
        # Save company
        company = Company(
            name=model.company_name,
            ticker=model.ticker,
            fiscal_year=model.base_year
        )
        session.add(company)
        
        # Save statements
        for stmt in model.historical_income_statements:
            income = IncomeStatementDB(
                company_id=company.id,
                period_end=stmt.period_end,
                revenue=stmt.revenue,
                net_income=stmt.net_income
            )
            session.add(income)
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
```

### 10. Real-time Data Integration

```python
import yfinance as yf

def get_live_data(ticker):
    """Fetch real-time financial data from Yahoo Finance."""
    stock = yf.Ticker(ticker)
    
    # Get financials
    income_stmt = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow
    
    # Convert to our schema
    statements = FinancialStatements(
        company_name=stock.info['longName'],
        ticker=ticker,
        fiscal_year=2023,
        report_type=ReportType.FORM_10K,
        accounting_standard=AccountingStandard.GAAP
    )
    
    # Parse and populate statements
    # ...
    
    return statements

# Usage
statements = get_live_data("AAPL")
model = ModelEngine(statements).build_linked_model()
```

## Testing Examples

### 11. Unit Tests

```python
import pytest
from src.core.model_engine import ModelEngine
from src.models.schemas import *

def test_model_validation():
    statements = create_test_statements()
    engine = ModelEngine(statements)
    model = engine.build_linked_model()
    
    assert model.is_balanced
    assert len(model.validation_errors) == 0

def test_forecast_growth():
    statements = create_test_statements()
    engine = ModelEngine(statements)
    model = engine.build_linked_model()
    
    forecast_engine = ForecastEngine(model)
    forecast = forecast_engine.forecast(years=3)
    
    # Check revenue growth
    base_revenue = model.historical_income_statements[-1].revenue
    forecast_revenue = forecast.forecast_income_statements[-1].revenue
    
    assert forecast_revenue > base_revenue
```

### 12. Integration Tests

```python
def test_full_pipeline():
    # Parse PDF
    parser = PDFParser("tests/data/sample_10k.pdf")
    data = parser.extract()
    
    assert data['total_pages'] > 0
    assert len(data['tables']) > 0
    
    # Classify
    classifier = GaapIfrsClassifier()
    standard, confidence, _ = classifier.classify(data['text'])
    
    assert standard in [AccountingStandard.GAAP, AccountingStandard.IFRS]
    assert confidence > 0.5
    
    # Build model
    statements = extract_statements(data)
    engine = ModelEngine(statements)
    model = engine.build_linked_model()
    
    assert model.is_balanced
```

## Performance Optimization

### 13. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_model(company_ticker, fiscal_year):
    """Cache frequently accessed models."""
    statements = load_statements(company_ticker, fiscal_year)
    engine = ModelEngine(statements)
    return engine.build_linked_model()
```

### 14. Async Processing

```python
import asyncio

async def process_report_async(pdf_path):
    loop = asyncio.get_event_loop()
    
    # Run CPU-intensive tasks in executor
    parser = PDFParser(pdf_path)
    data = await loop.run_in_executor(None, parser.extract)
    
    # Continue processing
    # ...
    
    return result

# Process multiple reports concurrently
async def process_multiple(pdf_paths):
    tasks = [process_report_async(path) for path in pdf_paths]
    results = await asyncio.gather(*tasks)
    return results
```

## Deployment Examples

### 15. Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 16. Cloud Function (AWS Lambda)

```python
import json
import boto3

def lambda_handler(event, context):
    # Get PDF from S3
    s3 = boto3.client('s3')
    bucket = event['bucket']
    key = event['key']
    
    # Download PDF
    s3.download_file(bucket, key, '/tmp/report.pdf')
    
    # Process
    parser = PDFParser('/tmp/report.pdf')
    data = parser.extract()
    # ... rest of pipeline
    
    # Upload result to S3
    s3.upload_file('/tmp/report.pdf', bucket, f'output/{key}')
    
    return {
        'statusCode': 200,
        'body': json.dumps('Analysis complete')
    }
```

## Monitoring & Logging

### 17. Structured Logging

```python
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level="INFO"
)
logger.add(
    "logs/app_{time}.log",
    rotation="100 MB",
    retention="30 days",
    compression="zip"
)

# Usage
logger.info("Processing report", company="AAPL", year=2023)
logger.error("Validation failed", errors=validation_errors)
```

### 18. Metrics Collection

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
reports_processed = Counter('reports_processed_total', 'Total reports processed')
processing_time = Histogram('report_processing_seconds', 'Time to process report')

@processing_time.time()
def process_report(pdf_path):
    # ... processing logic
    reports_processed.inc()
    return result

# Start metrics server
start_http_server(8000)
```
