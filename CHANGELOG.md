# Changelog

All notable changes to the Financial Alpha Intelligence project.

## [1.0.0] - 2026-01-13

### 🔥 Major Improvements
- **Advanced Architecture**: Refactored monolithic codebase into modular UI components and core engines.
- **Auto-Balancing Models**: 3-Statement models now automatically balance themselves using intelligent plugs.
- **Accurate Extraction**: Enhanced regex patterns for CAPEX, Dividends, and Working Capital from PDF reports.
- **Dynamic Assumptions**: Forecast assumptions are now derived from historical data (margins, DSO/DIO/DPO) rather than hardcoded values.
- **DCF Valuation Fixes**: Resolved issue with $0.00 implied share price by correctly sourcing share counts from Income Statements.

### 🏗 Technical Changes
- **Configuration Management**: Introduced `src/config.py` for centralized settings, following 12-factor app principles.
- **Exception Handling**: Added custom exception hierarchy in `src/exceptions.py`.
- **UI Modularization**: Split `app_streamlit.py` into `src/ui/` modules:
  - `market_pulse.py`
  - `report_analyzer.py`
  - `startup_valuator.py`
- **Testing**: Updated tests to reflect new auto-balancing logic.

### 🐛 Bug Fixes
- Fixed duplicate graph generation in report generator.
- Fixed dead code in reconciliation logic.
- Fixed infinite recursion in circular reference checks.
- Addressed "God File" anti-pattern in main app file.

### ⚠️ Known Issues
- Excel upload for Startup Valuator is in Beta.
- AI components (Sentiment/Summarizer) require High-RAM environment or API keys.
- PDF table extraction on large files (>50 pages) is limited to first 20 pages for performance.
