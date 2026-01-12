"""
Setup configuration for Financial Report Analyzer.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="finance-report-analyzer",
    version="0.1.0",
    author="Financial Modeling Team",
    author_email="team@example.com",
    description="AI-powered financial report analyzer with 3-statement modeling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/finance-report-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "pdfplumber>=0.10.0",
        "PyPDF2>=3.0.0",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.3",
        "camelot-py[cv]>=0.11.0",
        "tabula-py>=2.8.0",
        "matplotlib>=3.8.0",
        "plotly>=5.18.0",
        "seaborn>=0.13.0",
        "reportlab>=4.0.0",
        "weasyprint>=60.0",
        "jinja2>=3.1.2",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.0",
        "loguru>=0.7.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "jupyter>=1.0.0",
        ],
        "ai": [
            "transformers>=4.35.0",
            "spacy>=3.7.0",
            "openai>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "finance-analyzer=main:main",
        ],
    },
)
