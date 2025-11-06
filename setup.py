"""Setup script for AI Document Auditing System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-document-auditing",
    version="1.0.0",
    author="Arjun Sachar",
    author_email="arjun.sachar@ibm.com",
    description="A comprehensive document validation processor for articles with citation validation and confidence scoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/ai-document-auditing",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.9",
    install_requires=[
        "spacy>=3.7.0",
        "transformers>=4.35.0",
        "torch>=2.1.0",
        "sentence-transformers>=2.2.2",
        "nltk>=3.8.1",
        "anthropic>=0.7.0",
        "openai>=1.3.0",
        "requests>=2.31.0",
        "httpx>=0.25.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "pydantic>=2.5.0",
        "pyyaml>=6.0.1",
        "jsonlines>=4.0.0",
        "scikit-learn>=1.3.0",
        "fuzzywuzzy>=0.18.0",
        "python-levenshtein>=0.23.0",
        "textstat>=0.7.3",
        "textdistance>=4.6.0",
        "click>=8.1.0",
        "rich>=13.7.0",
        "loguru>=0.7.2",
        "tqdm>=4.66.0",
        "python-dotenv>=1.0.0",
        "pathlib2>=2.3.7",
        "dataclasses-json>=0.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-doc-audit=src.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "examples/*.json", "examples/*.md"],
    },
)
