"""
Main application entry point.
Example usage of the financial report analyzer.
"""

from pathlib import Path
from datetime import date
import sys

from loguru import logger

from src.core.pdf_parser import PDFParser
from src.core.gaap_ifrs_classifier import GaapIfrsClassifier
from src.core.model_engine import ModelEngine
from src.core.forecast_engine import ForecastEngine
from src.core.report_generator import ReportGenerator
from src.models.schemas import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    AccountingStandard,
    ReportType,
    Currency,
    ForecastAssumptions
)


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/analyzer_{time}.log",
        rotation="10 MB",
        retention="30 days",
        level="DEBUG"
    )


def analyze_financial_report(pdf_path: str, output_dir: str = "output", affinda_key: str = None):
    """
    Complete pipeline: PDF → Analysis → Forecast → Report
    
    Args:
        pdf_path: Path to financial report PDF
        output_dir: Directory for output files
    """
    logger.info("=" * 80)
    logger.info("FINANCIAL REPORT ANALYZER - STARTING")
    logger.info("=" * 80)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Step 1: Parse PDF
    logger.info("Step 1: Parsing PDF...")
    parser = PDFParser(pdf_path)
    extracted_data = parser.extract()
    
    logger.info(f"✓ Extracted {extracted_data['total_pages']} pages")
    logger.info(f"✓ Found {len(extracted_data['tables'])} tables")
    
    # Step 2: Classify accounting standard
    logger.info("\nStep 2: Classifying accounting standard...")
    classifier = GaapIfrsClassifier()
    standard, confidence, evidence = classifier.classify(
        extracted_data['text'],
        extracted_data['tables']
    )
    
    logger.info(f"✓ Detected standard: {standard.value} (confidence: {confidence:.1%})")
    

    # Step 3: Extract financial statements
    from src.core.financial_extractor import FinancialExtractor
    
    logger.info("\nStep 3: Extracting financial statements...")
    
    # Choose Extractor Strategy
    if affinda_key:
        from src.core.affinda_extractor import AffindaExtractor
        logger.info("🧠 Using Affinda AI for extraction...")
        try:
            ai_extractor = AffindaExtractor(affinda_key)
            statements = ai_extractor.extract(Path(pdf_path))
            logger.info(f"✓ AI Extraction Success: {statements.company_name}")
            logger.info(f"  Fiscal Year: {statements.fiscal_year}")
            logger.info(f"  Revenue: ${statements.income_statements[0].revenue:,.0f}")
        except Exception as e:
            logger.error(f"❌ AI Extraction failed: {e}")
            logger.info("Falling back to local keyword extraction...")
            statements = None
    else:
        statements = None

    if not statements:
        # Use local keyword-based extractor
        logger.info("Using local FinancialExtractor (Regex/Keyword)...")
        pages_dict = {i+1: text for i, text in enumerate(extracted_data['pages'])}
        extractor = FinancialExtractor(pages_dict)
        statements = extractor.extract()
        
        # Validation
        if statements.income_statements[0].revenue == 0:
             logger.warning("⚠️ Local Extractor found 0 Revenue.")
             logger.warning("Falling back to demo data structure for visualization only.")
             statements = create_sample_statements(standard)
             statements.company_name = "Analysis (Demo Data)" # Mark as demo
        else:
             logger.info(f"✓ Extracted data for {statements.company_name}")
             logger.info(f"  Revenue: ${statements.income_statements[0].revenue:,.0f}")
    
    # Step 4: Build linked model
    logger.info("\nStep 4: Building linked 3-statement model...")
    model_engine = ModelEngine(statements)
    linked_model = model_engine.build_linked_model()
    
    if linked_model.is_balanced:
        logger.info("✓ Model successfully linked and balanced")
    else:
        logger.warning(f"⚠ Model has {len(linked_model.validation_errors)} validation errors:")
        for error in linked_model.validation_errors[:5]:  # Show first 5
            logger.warning(f"  - {error}")
    
    # Step 5: Generate forecast
    logger.info("\nStep 5: Generating financial forecast...")
    
    forecast_assumptions = ForecastAssumptions(
        revenue_growth_rate=0.08,  # 8% annual growth
        gross_margin=0.42,
        operating_margin=0.22,
        tax_rate=0.21,
        capex_percent_of_revenue=0.06,
        days_sales_outstanding=45,
        days_inventory_outstanding=60,
        days_payable_outstanding=35
    )
    
    forecast_engine = ForecastEngine(linked_model)
    forecast_model = forecast_engine.forecast(
        years=5,
        assumptions=forecast_assumptions,
        scenario="base"
    )
    
    logger.info(f"✓ Generated {forecast_model.forecast_years}-year forecast")
    
    # Step 6: Generate PDF report
    logger.info("\nStep 6: Generating PDF report...")
    
    report_path = output_path / f"financial_analysis_{statements.company_name.replace(' ', '_')}.pdf"
    
    generator = ReportGenerator(forecast_model)
    generator.generate_pdf(str(report_path))
    
    logger.info(f"✓ Report saved to: {report_path}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 80)
    
    summary = model_engine.get_summary_metrics()
    logger.info(f"Company: {summary['company']}")
    logger.info(f"Fiscal Year: {summary['fiscal_year']}")
    logger.info(f"Revenue: ${summary['revenue']:,.0f}")
    logger.info(f"Net Income: ${summary['net_income']:,.0f}")
    logger.info(f"Net Margin: {summary['net_margin']:.1%}" if summary['net_margin'] else "Net Margin: N/A")
    logger.info(f"ROE: {summary['roe']:.1%}" if summary['roe'] else "ROE: N/A")
    
    return forecast_model


def create_sample_statements(standard: AccountingStandard) -> FinancialStatements:
    """
    Create sample financial statements for demonstration.
    In production, this would be replaced by actual extraction logic.
    """
    statements = FinancialStatements(
        company_name="TechCorp Inc.",
        ticker="TECH",
        fiscal_year=2023,
        report_type=ReportType.FORM_10K if standard == AccountingStandard.GAAP else ReportType.IFRS_ANNUAL,
        accounting_standard=standard,
        currency=Currency.USD
    )
    

    # Create 3 years of historical data
    for year in range(2023, 2026):
        # Income Statement
        base_revenue = 1_000_000_000 * (1.1 ** (year - 2023))
        
        income = IncomeStatement(
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            revenue=base_revenue,
            cost_of_revenue=base_revenue * 0.60,
            gross_profit=base_revenue * 0.40,
            operating_expenses=base_revenue * 0.20,
            operating_income=base_revenue * 0.20,
            depreciation_amortization=base_revenue * 0.05,
            ebitda=base_revenue * 0.25,
            ebit=base_revenue * 0.20,
            interest_expense=-base_revenue * 0.01,
            income_before_tax=base_revenue * 0.19,
            income_tax_expense=base_revenue * 0.19 * 0.21,
            net_income=base_revenue * 0.19 * 0.79,
            shares_outstanding_diluted=100_000_000,
            diluted_eps=(base_revenue * 0.19 * 0.79) / 100_000_000
        )
        statements.income_statements.append(income)
        
        # Balance Sheet
        bs = BalanceSheet(
            period_end=date(year, 12, 31),
            cash_and_equivalents=base_revenue * 0.15,
            accounts_receivable=base_revenue * 0.12,
            inventory=base_revenue * 0.10,
            total_current_assets=base_revenue * 0.40,
            property_plant_equipment_net=base_revenue * 0.50,
            intangible_assets=base_revenue * 0.20,
            total_assets=base_revenue * 1.20,
            accounts_payable=base_revenue * 0.08,
            short_term_debt=base_revenue * 0.05,
            total_current_liabilities=base_revenue * 0.15,
            long_term_debt=base_revenue * 0.30,
            total_liabilities=base_revenue * 0.45,
            retained_earnings=base_revenue * 0.60,
            total_shareholders_equity=base_revenue * 0.75
        )
        statements.balance_sheets.append(bs)
        
        # Cash Flow Statement
        cf = CashFlowStatement(
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            net_income=income.net_income,
            depreciation_amortization=income.depreciation_amortization,
            changes_in_working_capital=-base_revenue * 0.02,
            cash_from_operations=income.net_income + income.depreciation_amortization - base_revenue * 0.02,
            capital_expenditures=-base_revenue * 0.06,
            cash_from_investing=-base_revenue * 0.06,
            dividends_paid=-income.net_income * 0.30,
            cash_from_financing=-income.net_income * 0.30,
            net_change_in_cash=base_revenue * 0.02,
            cash_beginning_of_period=base_revenue * 0.13 if year > 2021 else base_revenue * 0.13,
            cash_end_of_period=base_revenue * 0.15
        )
        statements.cash_flow_statements.append(cf)
    
    return statements


def main():
    """Main entry point."""
    setup_logging()
    
    # Example 1: Analyze a PDF file
    # analyze_financial_report("data/sample_reports/apple_10k_2023.pdf")
    
    # Example 2: Use sample data for demonstration
    logger.info("Running with sample data (no PDF input)")
    
    # Create sample statements
    statements = create_sample_statements(AccountingStandard.GAAP)
    
    # Build model
    model_engine = ModelEngine(statements)
    linked_model = model_engine.build_linked_model()
    
    # Forecast
    forecast_engine = ForecastEngine(linked_model)
    forecast_model = forecast_engine.forecast(years=5, scenario="base")
    
    # Generate report
    Path("output").mkdir(exist_ok=True)
    generator = ReportGenerator(forecast_model)
    generator.generate_pdf("output/sample_financial_report.pdf")
    
    logger.info("✓ Sample report generated: output/sample_financial_report.pdf")


if __name__ == "__main__":
    main()
