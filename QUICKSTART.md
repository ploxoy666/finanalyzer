# 🚀 Quick Start Guide

## Installation

### Prerequisites
- Python 3.9 or higher
- Tesseract OCR (for scanned PDFs)
- Git

### Step 1: Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Step 2: Clone and Setup

```bash
# Clone the repository (or download the project)
cd "/Users/light/Desktop/finance report analyzer"

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import pdfplumber; import pandas; print('✓ Installation successful!')"
```

---

## Running Your First Analysis

### Option 1: Use Sample Data (Recommended for First Run)

```bash
python main.py
```

This will:
- Create sample financial statements
- Build a linked 3-statement model
- Generate a 5-year forecast
- Create a PDF report in `output/sample_financial_report.pdf`

**Expected output:**
```
[INFO] Running with sample data (no PDF input)
[INFO] Initialized ModelEngine for TechCorp Inc.
[INFO] Building linked 3-statement model...
[INFO] ✓ Model successfully linked and balanced
[INFO] Generating 5-year base forecast...
[INFO] ✓ Generated 5-year forecast
[INFO] Generating PDF report: output/sample_financial_report.pdf
[INFO] ✓ PDF report generated
[INFO] ✓ Sample report generated: output/sample_financial_report.pdf
```

### Option 2: Analyze a Real PDF

```python
from main import analyze_financial_report

# Analyze a 10-K or annual report
analyze_financial_report(
    pdf_path="path/to/your/10k.pdf",
    output_dir="output"
)
```

### Option 3: Interactive Jupyter Notebook

```bash
# Install Jupyter (if not already installed)
pip install jupyter

# Launch notebook
jupyter notebook notebooks/financial_analysis_demo.ipynb
```

---

## Basic Usage Examples

### Example 1: Simple Analysis

```python
from datetime import date
from src.core.model_engine import ModelEngine
from src.core.forecast_engine import ForecastEngine
from src.core.report_generator import ReportGenerator
from src.models.schemas import *

# Create financial statements
statements = FinancialStatements(
    company_name="My Company",
    ticker="MYCO",
    fiscal_year=2023,
    report_type=ReportType.FORM_10K,
    accounting_standard=AccountingStandard.GAAP
)

# Add income statement
income = IncomeStatement(
    period_start=date(2023, 1, 1),
    period_end=date(2023, 12, 31),
    revenue=1_000_000_000,
    cost_of_revenue=600_000_000,
    gross_profit=400_000_000,
    operating_income=200_000_000,
    net_income=150_000_000
)
statements.income_statements.append(income)

# Add balance sheet
bs = BalanceSheet(
    period_end=date(2023, 12, 31),
    cash_and_equivalents=100_000_000,
    total_current_assets=400_000_000,
    total_assets=1_200_000_000,
    total_current_liabilities=200_000_000,
    total_liabilities=500_000_000,
    total_shareholders_equity=700_000_000
)
statements.balance_sheets.append(bs)

# Build model
engine = ModelEngine(statements)
model = engine.build_linked_model()

# Generate forecast
forecast_engine = ForecastEngine(model)
forecast = forecast_engine.forecast(years=5)

# Create report
generator = ReportGenerator(forecast)
generator.generate_pdf("output/my_analysis.pdf")

print("✓ Analysis complete!")
```

### Example 2: GAAP vs IFRS Classification

```python
from src.core.gaap_ifrs_classifier import GaapIfrsClassifier

# Sample text from financial report
text = """
The consolidated financial statements have been prepared in 
accordance with International Financial Reporting Standards (IFRS).
We use the revaluation model for property, plant and equipment.
"""

classifier = GaapIfrsClassifier()
standard, confidence, evidence = classifier.classify(text)

print(f"Standard: {standard.value}")
print(f"Confidence: {confidence:.1%}")
```

### Example 3: Custom Forecast Assumptions

```python
from src.models.schemas import ForecastAssumptions

# Define custom assumptions
assumptions = ForecastAssumptions(
    revenue_growth_rate=0.12,      # 12% annual growth
    gross_margin=0.45,             # 45% gross margin
    operating_margin=0.25,         # 25% operating margin
    tax_rate=0.21,                 # 21% tax rate
    capex_percent_of_revenue=0.08, # 8% CAPEX
    days_sales_outstanding=40,     # 40 days DSO
    days_inventory_outstanding=50, # 50 days DIO
    days_payable_outstanding=30    # 30 days DPO
)

# Generate forecast with custom assumptions
forecast = forecast_engine.forecast(
    years=5,
    assumptions=assumptions,
    scenario="bull"  # or "base" or "bear"
)
```

---

## Project Structure Overview

```
finance-report-analyzer/
├── main.py                    # Main entry point
├── src/
│   ├── core/                  # Core modules
│   │   ├── pdf_parser.py      # PDF parsing & OCR
│   │   ├── gaap_ifrs_classifier.py  # Standards detection
│   │   ├── model_engine.py    # 3-statement linking
│   │   ├── forecast_engine.py # Forecasting logic
│   │   └── report_generator.py # PDF generation
│   └── models/
│       └── schemas.py         # Data models
├── notebooks/                 # Jupyter notebooks
├── output/                    # Generated reports
├── data/                      # Input data
└── tests/                     # Unit tests
```

---

## Common Issues & Solutions

### Issue 1: Tesseract not found
```
Error: pytesseract.pytesseract.TesseractNotFoundError
```

**Solution:**
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Windows - add Tesseract to PATH or specify location:
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Issue 2: PDF table extraction fails
```
Error: No tables found in PDF
```

**Solution:**
- Ensure PDF is not password-protected
- Try different extraction methods (camelot vs tabula)
- For scanned PDFs, use OCR mode

### Issue 3: Memory error with large PDFs
```
Error: MemoryError
```

**Solution:**
```python
# Process PDF in chunks
parser = PDFParser(pdf_path)
for page_num in range(1, total_pages, 10):
    data = parser.extract_page_range(page_num, page_num + 9)
```

---

## Next Steps

1. **Explore Examples**: Check `EXAMPLES.md` for advanced usage
2. **Read Architecture**: See `ARCHITECTURE.md` for technical details
3. **Try Jupyter Notebook**: Interactive analysis in `notebooks/`
4. **Run Tests**: `pytest tests/` (after implementing tests)
5. **Customize**: Modify assumptions and templates

---

## Getting Help

- **Documentation**: See `README.md` and `ARCHITECTURE.md`
- **Examples**: Check `EXAMPLES.md`
- **Issues**: Review common issues above
- **Community**: (Add your community links here)

---

## Performance Tips

1. **Use digital PDFs** when possible (faster than OCR)
2. **Cache results** for frequently analyzed companies
3. **Batch process** multiple reports
4. **Use async processing** for large workloads
5. **Optimize assumptions** for faster convergence

---

## What's Next?

After running your first analysis, you can:

- ✅ Analyze real 10-K reports
- ✅ Compare multiple companies
- ✅ Build custom forecast scenarios
- ✅ Export to Excel for further analysis
- ✅ Integrate with your existing tools
- ✅ Deploy as a web service (see `SAAS_ROADMAP.md`)

**Happy Analyzing! 📊**
