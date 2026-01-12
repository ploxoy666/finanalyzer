"""
Unit tests for Financial Model Engine.
"""

import pytest
from datetime import date

from src.core.model_engine import ModelEngine
from src.models.schemas import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    AccountingStandard,
    ReportType,
    Currency
)


@pytest.fixture
def sample_statements():
    """Create sample financial statements for testing."""
    statements = FinancialStatements(
        company_name="Test Corp",
        ticker="TEST",
        fiscal_year=2023,
        report_type=ReportType.FORM_10K,
        accounting_standard=AccountingStandard.GAAP,
        currency=Currency.USD
    )
    
    # Year 1
    statements.income_statements.append(
        IncomeStatement(
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            revenue=1_000_000_000,
            cost_of_revenue=600_000_000,
            gross_profit=400_000_000,
            operating_expenses=200_000_000,
            operating_income=200_000_000,
            depreciation_amortization=50_000_000,
            net_income=150_000_000
        )
    )
    
    statements.balance_sheets.append(
        BalanceSheet(
            period_end=date(2023, 12, 31),
            cash_and_equivalents=150_000_000,
            accounts_receivable=120_000_000,
            inventory=100_000_000,
            total_current_assets=400_000_000,
            property_plant_equipment_net=500_000_000,
            total_assets=1_200_000_000,
            accounts_payable=80_000_000,
            total_current_liabilities=150_000_000,
            total_liabilities=450_000_000,
            retained_earnings=600_000_000,
            total_shareholders_equity=750_000_000
        )
    )
    
    statements.cash_flow_statements.append(
        CashFlowStatement(
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            net_income=150_000_000,
            depreciation_amortization=50_000_000,
            changes_in_working_capital=-20_000_000,
            cash_from_operations=180_000_000,
            capital_expenditures=-60_000_000,
            cash_from_investing=-60_000_000,
            dividends_paid=-45_000_000,
            cash_from_financing=-45_000_000,
            net_change_in_cash=75_000_000
        )
    )
    
    return statements


class TestModelEngine:
    """Test cases for ModelEngine."""
    
    def test_initialization(self, sample_statements):
        """Test model engine initialization."""
        engine = ModelEngine(sample_statements)
        assert engine.statements == sample_statements
        assert engine.validation_errors == []
    
    def test_build_linked_model(self, sample_statements):
        """Test building linked model."""
        engine = ModelEngine(sample_statements)
        model = engine.build_linked_model()
        
        assert model is not None
        assert model.company_name == "Test Corp"
        assert len(model.historical_income_statements) == 1
        assert len(model.historical_balance_sheets) == 1
        assert len(model.historical_cash_flows) == 1
    
    def test_balance_sheet_validation(self, sample_statements):
        """Test balance sheet balancing."""
        engine = ModelEngine(sample_statements)
        model = engine.build_linked_model()
        
        bs = model.historical_balance_sheets[0]
        
        # Assets = Liabilities + Equity
        assert abs(bs.total_assets - (bs.total_liabilities + bs.total_shareholders_equity)) < 1
    
    def test_ratio_calculation(self, sample_statements):
        """Test financial ratio calculations."""
        engine = ModelEngine(sample_statements)
        model = engine.build_linked_model()
        
        assert len(model.historical_ratios) > 0
        
        ratios = model.historical_ratios[0]
        
        # Check profitability ratios
        assert ratios.gross_margin is not None
        assert 0 <= ratios.gross_margin <= 1
        
        assert ratios.net_margin is not None
        assert 0 <= ratios.net_margin <= 1
        
        # Check liquidity ratios
        if ratios.current_ratio:
            assert ratios.current_ratio > 0
    
    def test_summary_metrics(self, sample_statements):
        """Test summary metrics generation."""
        engine = ModelEngine(sample_statements)
        model = engine.build_linked_model()
        
        summary = engine.get_summary_metrics()
        
        assert summary['company'] == "Test Corp"
        assert summary['fiscal_year'] == 2023
        assert summary['revenue'] == 1_000_000_000
        assert summary['net_income'] == 150_000_000
    
    def test_validation_with_invalid_data(self):
        """Test validation with unbalanced data."""
        statements = FinancialStatements(
            company_name="Invalid Corp",
            ticker="INV",
            fiscal_year=2023,
            report_type=ReportType.FORM_10K,
            accounting_standard=AccountingStandard.GAAP
        )
        
        # Create unbalanced balance sheet
        statements.balance_sheets.append(
            BalanceSheet(
                period_end=date(2023, 12, 31),
                total_assets=1_000_000,
                total_liabilities=500_000,
                total_shareholders_equity=400_000  # Doesn't balance!
            )
        )
        
        statements.income_statements.append(
            IncomeStatement(
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
                revenue=1_000_000,
                net_income=100_000
            )
        )
        
        statements.cash_flow_statements.append(
            CashFlowStatement(
                period_start=date(2023, 1, 1),
                period_end=date(2023, 12, 31),
                cash_from_operations=100_000
            )
        )
        
        engine = ModelEngine(statements)
        model = engine.build_linked_model()
        
        # Should have validation errors
        assert not model.is_balanced
        assert len(model.validation_errors) > 0


class TestMultiPeriodModel:
    """Test cases for multi-period models."""
    
    def test_multi_year_model(self):
        """Test model with multiple years of data."""
        statements = FinancialStatements(
            company_name="Multi Year Corp",
            ticker="MYC",
            fiscal_year=2023,
            report_type=ReportType.FORM_10K,
            accounting_standard=AccountingStandard.GAAP
        )
        
        # Add 3 years of data
        for year in range(2021, 2024):
            base_revenue = 1_000_000_000 * (1.1 ** (year - 2021))
            
            statements.income_statements.append(
                IncomeStatement(
                    period_start=date(year, 1, 1),
                    period_end=date(year, 12, 31),
                    revenue=base_revenue,
                    net_income=base_revenue * 0.15
                )
            )
            
            statements.balance_sheets.append(
                BalanceSheet(
                    period_end=date(year, 12, 31),
                    total_assets=base_revenue * 1.2,
                    total_liabilities=base_revenue * 0.45,
                    total_shareholders_equity=base_revenue * 0.75
                )
            )
            
            statements.cash_flow_statements.append(
                CashFlowStatement(
                    period_start=date(year, 1, 1),
                    period_end=date(year, 12, 31),
                    cash_from_operations=base_revenue * 0.20
                )
            )
        
        engine = ModelEngine(statements)
        model = engine.build_linked_model()
        
        assert len(model.historical_income_statements) == 3
        assert len(model.historical_balance_sheets) == 3
        assert len(model.historical_cash_flows) == 3
        assert len(model.historical_ratios) == 3


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
