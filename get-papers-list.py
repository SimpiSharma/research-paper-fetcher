"""
PubMed Research Paper Fetcher

This program fetches research papers from PubMed based on user-specified queries,
identifying papers with at least one author affiliated with pharmaceutical or biotech companies.
Results are saved as a CSV file with detailed information about each paper.

Requirements:
- Python 3.7+
- Dependencies: requests, pandas, python-dateutil
- Install with: poetry install

Usage:
python get-papers-list.py [options]

Options:
-h, --help      Show help message
-d, --debug     Enable debug mode
-f, --file      Specify output filename (default: pubmed_results.csv)

Example:
python get-papers-list.py -d -f my_results.csv
"""

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus
import time

try:
    import requests
    from dateutil.parser import parse as parse_date
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("Please install dependencies with: poetry install")
    sys.exit(1)


class PubMedFetcher:
    """Fetches and processes research papers from PubMed API."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Common pharmaceutical and biotech company patterns
    PHARMA_BIOTECH_PATTERNS = [
        # Major pharmaceutical companies
        r'\b(pfizer|novartis|roche|johnson\s*&\s*johnson|j&j|merck|gsk|glaxosmithkline|sanofi|astrazeneca|abbvie|bristol\s*myers\s*squibb|eli\s*lilly|boehringer\s*ingelheim|takeda|bayer|amgen|gilead|biogen|celgene|vertex|regeneron|alexion|incyte|illumina|moderna|biontech)\b',
        
        # Generic biotech/pharma indicators
        r'\b(pharmaceuticals?|biotech|biotechnology|therapeutics?|biopharmaceuticals?|life\s*sciences?|drug\s*development|clinical\s*research)\b',
        
        # Research institutions with pharma connections
        r'\b(pharma|biotech|therapeutic|clinical)\s+(research|institute|center|laboratory|lab)\b',
        
        # Company suffixes
        r'\b\w+\s*(pharmaceuticals?|biotech|therapeutics?|biosciences?|lifesciences?)\b'
    ]
    
    def __init__(self, debug: bool = False):
        """Initialize the PubMed fetcher."""
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PubMedFetcher/1.0 (research tool)'
        })
        
        # Set up logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('pubmed_fetcher.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search PubMed for papers matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of PubMed IDs
        """
        self.logger.info(f"Searching PubMed for: {query}")
        
        search_url = f"{self.BASE_URL}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'sort': 'relevance'
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            id_list = data.get('esearchresult', {}).get('idlist', [])
            
            self.logger.info(f"Found {len(id_list)} papers")
            return id_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error searching PubMed: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing search response: {e}")
            return []
    
    def fetch_paper_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for a list of PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of paper details dictionaries
        """
        if not pmids:
            return []
        
        self.logger.info(f"Fetching details for {len(pmids)} papers")
        
        fetch_url = f"{self.BASE_URL}efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        try:
            response = self.session.get(fetch_url, params=params, timeout=60)
            response.raise_for_status()
            
            return self._parse_xml_response(response.text)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching paper details: {e}")
            return []
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict]:
        """Parse XML response and extract paper information."""
        papers = []
        
        # Simple XML parsing without external libraries
        # This is a basic implementation - in production, use xml.etree.ElementTree
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                paper_info = self._extract_paper_info(article)
                if paper_info:
                    papers.append(paper_info)
                    
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML: {e}")
        
        return papers
    
    def _extract_paper_info(self, article_elem) -> Optional[Dict]:
        """Extract information from a single article XML element."""
        try:
            # Extract PMID
            pmid_elem = article_elem.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else "N/A"
            
            # Extract title
            title_elem = article_elem.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "N/A"
            
            # Extract publication date
            pub_date = self._extract_publication_date(article_elem)
            
            # Extract authors and affiliations
            authors_info = self._extract_authors_and_affiliations(article_elem)
            
            # Check if any author has pharma/biotech affiliation
            pharma_authors = self._filter_pharma_authors(authors_info)
            company_affiliations = self._extract_company_names(authors_info)
            
            # Only include papers with pharma/biotech affiliations
            if not pharma_authors:
                return None
            
            # Extract corresponding author email
            corresponding_email = self._extract_corresponding_email(authors_info)
            
            return {
                'PubmedID': pmid,
                'Title': title,
                'Publication Date': pub_date,
                'Non-academic Author(s)': '; '.join(pharma_authors),
                'Company Affiliation(s)': '; '.join(company_affiliations),
                'Corresponding Author Email': corresponding_email
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting paper info: {e}")
            return None
    
    def _extract_publication_date(self, article_elem) -> str:
        """Extract publication date from article element."""
        # Try different date elements
        date_elements = [
            './/PubDate',
            './/ArticleDate',
            './/DateCompleted'
        ]
        
        for date_path in date_elements:
            date_elem = article_elem.find(date_path)
            if date_elem is not None:
                year = date_elem.find('Year')
                month = date_elem.find('Month')
                day = date_elem.find('Day')
                
                if year is not None:
                    date_str = year.text
                    if month is not None:
                        date_str += f"-{month.text}"
                        if day is not None:
                            date_str += f"-{day.text}"
                    return date_str
        
        return "N/A"
    
    def _extract_authors_and_affiliations(self, article_elem) -> List[Dict]:
        """Extract authors and their affiliations."""
        authors = []
        
        author_list = article_elem.find('.//AuthorList')
        if author_list is not None:
            for author_elem in author_list.findall('Author'):
                author_info = {}
                
                # Extract author name
                last_name = author_elem.find('LastName')
                first_name = author_elem.find('ForeName')
                
                if last_name is not None:
                    name = last_name.text
                    if first_name is not None:
                        name += f", {first_name.text}"
                    author_info['name'] = name
                
                # Extract affiliations
                affiliations = []
                affiliation_list = author_elem.find('AffiliationInfo')
                if affiliation_list is not None:
                    for affil_elem in affiliation_list.findall('Affiliation'):
                        if affil_elem.text:
                            affiliations.append(affil_elem.text)
                
                author_info['affiliations'] = affiliations
                
                # Check for corresponding author
                author_info['is_corresponding'] = self._is_corresponding_author(author_elem)
                
                authors.append(author_info)
        
        return authors
    
    def _is_corresponding_author(self, author_elem) -> bool:
        """Check if author is corresponding author."""
        # Look for corresponding author indicators
        for elem in author_elem.iter():
            if elem.text and 'corresponding' in elem.text.lower():
                return True
        return False
    
    def _filter_pharma_authors(self, authors_info: List[Dict]) -> List[str]:
        """Filter authors with pharmaceutical/biotech affiliations."""
        pharma_authors = []
        
        for author in authors_info:
            if 'name' in author and 'affiliations' in author:
                for affiliation in author['affiliations']:
                    if self._is_pharma_affiliation(affiliation):
                        pharma_authors.append(author['name'])
                        break
        
        return pharma_authors
    
    def _is_pharma_affiliation(self, affiliation: str) -> bool:
        """Check if affiliation is pharmaceutical/biotech related."""
        affiliation_lower = affiliation.lower()
        
        for pattern in self.PHARMA_BIOTECH_PATTERNS:
            if re.search(pattern, affiliation_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_company_names(self, authors_info: List[Dict]) -> List[str]:
        """Extract company names from affiliations."""
        companies = set()
        
        for author in authors_info:
            if 'affiliations' in author:
                for affiliation in author['affiliations']:
                    if self._is_pharma_affiliation(affiliation):
                        # Extract company name (simplified)
                        company = self._parse_company_name(affiliation)
                        if company:
                            companies.add(company)
        
        return list(companies)
    
    def _parse_company_name(self, affiliation: str) -> Optional[str]:
        """Parse company name from affiliation string."""
        # Simple parsing - extract text before common delimiters
        for delimiter in [',', ';', '\n', '  ']:
            if delimiter in affiliation:
                parts = affiliation.split(delimiter)
                for part in parts:
                    if self._is_pharma_affiliation(part):
                        return part.strip()
        
        return affiliation.strip()
    
    def _extract_corresponding_email(self, authors_info: List[Dict]) -> str:
        """Extract corresponding author email."""
        # This is a simplified implementation
        # In practice, email extraction from PubMed is complex
        for author in authors_info:
            if author.get('is_corresponding', False):
                # Look for email in affiliations
                for affiliation in author.get('affiliations', []):
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', affiliation)
                    if email_match:
                        return email_match.group()
        
        return "N/A"
    
    def save_to_csv(self, papers: List[Dict], filename: str) -> None:
        """Save papers to CSV file."""
        if not papers:
            self.logger.warning("No papers to save")
            return
        
        self.logger.info(f"Saving {len(papers)} papers to {filename}")
        
        fieldnames = [
            'PubmedID',
            'Title',
            'Publication Date',
            'Non-academic Author(s)',
            'Company Affiliation(s)',
            'Corresponding Author Email'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(papers)
            
            self.logger.info(f"Successfully saved results to {filename}")
            
        except IOError as e:
            self.logger.error(f"Error saving CSV file: {e}")
    
    def run(self, query: str, filename: str = "pubmed_results.csv", max_results: int = 100) -> None:
        """Main execution method."""
        self.logger.info("Starting PubMed paper fetcher")
        
        # Search for papers
        pmids = self.search_pubmed(query, max_results)
        
        if not pmids:
            self.logger.warning("No papers found for the query")
            return
        
        # Fetch detailed information
        papers = self.fetch_paper_details(pmids)
        
        if not papers:
            self.logger.warning("No papers with pharma/biotech affiliations found")
            return
        
        # Save results
        self.save_to_csv(papers, filename)
        
        self.logger.info(f"Process completed. Found {len(papers)} relevant papers.")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Fetch research papers from PubMed with pharmaceutical/biotech affiliations"
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '-f', '--file',
        default='pubmed_results.csv',
        help='Output filename (default: pubmed_results.csv)'
    )
    
    args = parser.parse_args()
    
    # Get user query
    print("PubMed Research Paper Fetcher")
    print("=" * 40)
    print("This tool fetches research papers from PubMed and identifies those")
    print("with authors affiliated with pharmaceutical or biotech companies.")
    print()
    
    query = input("Enter your search query: ").strip()
    
    if not query:
        print("Error: Please provide a search query")
        sys.exit(1)
    
    max_results = 100
    try:
        max_input = input(f"Maximum results to fetch (default: {max_results}): ").strip()
        if max_input:
            max_results = int(max_input)
    except ValueError:
        print("Invalid number, using default value")
    
    # Initialize and run fetcher
    fetcher = PubMedFetcher(debug=args.debug)
    
    try:
        fetcher.run(query, args.file, max_results)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
