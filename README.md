# PubMed Research Paper Fetcher

A Python program to fetch research papers from PubMed based on user-specified queries, identifying papers with at least one author affiliated with pharmaceutical or biotech companies. Results are returned as a CSV file with detailed information about each paper.

## Features

- **PubMed API Integration**: Uses the official NCBI E-utilities API for reliable data retrieval
- **Pharmaceutical/Biotech Detection**: Automatically identifies papers with authors from pharmaceutical and biotech companies
- **Comprehensive Data Extraction**: Extracts PubMed ID, title, publication date, author affiliations, and corresponding author emails
- **Flexible Query Support**: Supports PubMed's full query syntax for complex searches
- **CSV Export**: Results are saved in a structured CSV format for easy analysis
- **Error Handling**: Robust error handling for API failures and malformed data
- **Logging**: Comprehensive logging for debugging and monitoring

## Requirements

- Python 3.7 or higher
- Poetry for dependency management
- Internet connection for API access

## Installation

1. **Clone or download the project files**

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Usage

### Basic Usage

Run the program interactively:
```bash
python get-papers-list.py
```

The program will prompt you for:
- Search query (supports full PubMed query syntax)
- Maximum number of results to fetch (default: 100)

### Command Line Options

```bash
python get-papers-list.py [options]
```

**Options:**
- `-h, --help`: Show help message
- `-d, --debug`: Enable debug mode for detailed logging
- `-f, --file FILENAME`: Specify output filename (default: pubmed_results.csv)

### Examples

1. **Basic search with debug output:**
   ```bash
   python get-papers-list.py -d
   ```

2. **Search with custom output file:**
   ```bash
   python get-papers-list.py -f cancer_research.csv
   ```

3. **Debug mode with custom filename:**
   ```bash
   python get-papers-list.py -d -f diabetes_papers.csv
   ```

### Query Examples

When prompted for a search query, you can use:

- **Simple keywords**: `cancer treatment`
- **Author search**: `Smith J[Author]`
- **Date range**: `2020:2023[PDAT]`
- **Journal specific**: `Nature[Journal]`
- **Complex queries**: `(cancer OR tumor) AND (treatment OR therapy) AND 2022:2023[PDAT]`

## Output Format

The program generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `PubmedID` | Unique PubMed identifier |
| `Title` | Paper title |
| `Publication Date` | Date of publication |
| `Non-academic Author(s)` | Names of authors with pharma/biotech affiliations |
| `Company Affiliation(s)` | Names of pharmaceutical/biotech companies |
| `Corresponding Author Email` | Email address of corresponding author |

## How It Works

1. **Search Phase**: Queries PubMed using the E-utilities API
2. **Filtering Phase**: Fetches detailed paper information and identifies pharmaceutical/biotech affiliations
3. **Processing Phase**: Extracts relevant information and author details
4. **Export Phase**: Saves filtered results to CSV

### Company Detection

The program identifies pharmaceutical and biotech companies using:

- **Known company names**: Pfizer, Novartis, Roche, J&J, Merck, GSK, etc.
- **Industry keywords**: pharmaceuticals, biotech, therapeutics, biopharmaceuticals
- **Institution patterns**: pharma research centers, biotech labs
- **Company suffixes**: "Pharmaceuticals", "Biotech", "Therapeutics"

## Project Structure

```
pubmed-fetcher/
├── get-papers-list.py      # Main executable script
├── pyproject.toml          # Poetry configuration
├── README.md              # This file
└── pubmed_fetcher.log     # Log file (generated during execution)
```

## Error Handling

The program includes comprehensive error handling for:

- **Network issues**: API timeouts, connection errors
- **API errors**: Invalid queries, rate limiting
- **Data parsing errors**: Malformed XML responses
- **File system errors**: Permission issues, disk space

## Logging

- **Console output**: Real-time progress and status updates
- **Log file**: Detailed logging saved to `pubmed_fetcher.log`
- **Debug mode**: Enhanced logging with `-d` flag

## Performance Considerations

- **API rate limiting**: Respects NCBI's usage guidelines
- **Batch processing**: Efficiently processes multiple papers
- **Memory management**: Handles large result sets appropriately
- **Timeout handling**: Configurable timeouts for API calls

## Dependencies

The program uses these Python packages:

- `requests`: HTTP client for API calls
- `python-dateutil`: Date parsing and manipulation
- `pandas`: Data processing (optional, for enhanced CSV handling)

## Contributing

When contributing to this project:

1. Follow PEP 8 style guidelines
2. Add type hints for new functions
3. Include comprehensive error handling
4. Update documentation for new features
5. Add tests for new functionality

## License

This project is provided as-is for educational and research purposes. Please respect PubMed's terms of service and usage guidelines when using this tool.

## Troubleshooting

### Common Issues

1. **"No papers found"**: Check your query syntax and try broader terms
2. **API timeout errors**: Reduce the number of results or try again later
3. **Permission errors**: Ensure you have write access to the output directory
4. **Missing dependencies**: Run `poetry install` to install all requirements

### Getting Help

- Check the log file (`pubmed_fetcher.log`) for detailed error information
- Use debug mode (`-d`) for verbose output
- Verify your internet connection and PubMed API access

## Version History

- **v1.0.0**: Initial release with core functionality
  - PubMed API integration
  - Pharmaceutical/biotech company detection
  - CSV export functionality
  - Command-line interface
  - Comprehensive error handling and logging
