import os
import re
import requests
from pyairtable import Table
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
import spacy

import certifi
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import re



# Set up Airtable API details
AIRTABLE_API_KEY = 'patvS8osFDngCE0iW.4728217ddb2f14ecb1a3267e685ea11382100608c5f39205d0249eae7b8356c3'
BASE_ID = 'appMoJrdRNUc086rC'
TABLE_NAME = 'Bandi online (clone)'  # Your table name
PDF_FIELD_NAME = 'PDF'  # Your attachment field name

# Define your view name here
VIEW_NAME = 'open'  # Airtable view to read from

# Specify the row number to start from (1-based index)
START_ROW = 1  # Change this to the desired row number

# Initialize Airtable connection
table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)

# Directory to store downloaded PDFs
DOWNLOAD_DIR = 'pdfs'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Directory to store text files
TEXT_DIR = 'text_files'
if not os.path.exists(TEXT_DIR):
    os.makedirs(TEXT_DIR)

# Load the Italian NLP model
nlp = spacy.load("it_core_news_sm")

# Download NLTK stopwords if not already installed
nltk.download('stopwords')
italian_stopwords = set(stopwords.words('italian'))

# Add custom stopwords if needed
custom_stopwords = {"per", "di", "con", "e", "a", "il", "la", "le", "un", "una", "d'", "d", "lo", "l"}

def preserve_entities(text):
    """Preserve legal references and special entities like laws and codes."""
    # Preserve patterns such as "art. 42", "L.R. n. 34/2008"
    law_patterns = re.compile(r'(art\. \d+|L\.R\. n\.\s\d+/\d{4})', re.IGNORECASE)
    matches = law_patterns.findall(text)

    # Replace special entities with a placeholder
    for match in matches:
        text = text.replace(match, f" {match} ")

    return text

def clean_text_with_preserved_entities(text):
    """Clean text by removing stopwords and preserving legal references and structure."""
    # Step 1: Convert text to lowercase
    text = text.lower()

    # Step 2: Preserve important entities such as legal references
    text = preserve_entities(text)

    # Step 3: Remove special characters, keeping only alphanumeric, space, and preserved tokens
    text = re.sub(r'(?<=\d)%|[^a-zA-Z0-9%\s]', '', text)


    # Step 4: Tokenize text by splitting into words
    tokens = text.split()

    # Step 5: Filter tokens to remove stopwords, custom stopwords, and unnecessary spaces
    cleaned_tokens = [token for token in tokens if token not in italian_stopwords and token not in custom_stopwords and token.strip() != '']

    # Step 6: Rejoin cleaned tokens into a cleaned text string
    cleaned_text = " ".join(cleaned_tokens)

    return cleaned_text
def clean_text(text):
    """Clean text by removing stopwords and preserving legal references and structure."""
    # Step 1: Convert text to lowercase
    text = text.lower()




    # Step 3: Remove special characters, keeping only alphanumeric, space, and preserved tokens
    text = re.sub(r'(?<=\d)%|[^a-zA-Z0-9%\s]', '', text)


    # Step 4: Tokenize text by splitting into words
    tokens = text.split()

    # Step 5: Filter tokens to remove stopwords, custom stopwords, and unnecessary spaces
    cleaned_tokens = [token for token in tokens if token not in italian_stopwords and token not in custom_stopwords and token.strip() != '']

    # Step 6: Rejoin cleaned tokens into a cleaned text string
    cleaned_text = " ".join(cleaned_tokens)

    return cleaned_text

def maintain_structure(text):
    """
    Preserve the essential structure such as section numbers and headings.
    Ensures that section headers like '1.', '1.1' are maintained with added clarity.
    """
    # Add newlines around section numbers for better readability
    # e.g., "1." or "1.1" will have newlines added before and after for separation
    structured_text = re.sub(r'(\d+\.\d*)', r'\n\1\n', text)

    # Add extra spacing between capitalized section headers (like A., B.)
    structured_text = re.sub(r'([A-Z]\.)', r'\n\1\n', structured_text)

    # Ensure proper formatting for readability
    return structured_text


def download_pdf(pdf_url, filename):
    """
    Downloads the PDF file from Airtable attachment URL.
    """
    response = requests.get(pdf_url)
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file, handling both text-based and scanned PDFs.
    """
    text = ''

    try:
        # First, try extracting text from text-based PDFs using PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text
    except Exception as e:
        print(f"Error reading PDF with PyPDF2: {e}")

    # If no text was extracted (e.g., scanned PDF), use OCR via pytesseract
    if not text.strip():
        print(f"No text extracted from {pdf_path}. Attempting OCR...")
        images = convert_from_path(pdf_path)
        for image in images:
            text += pytesseract.image_to_string(image)

    return text


def save_text_to_file(filename, text):
    """Saves the extracted text to a .txt file with the same filename as the PDF."""
    # Create a new filename by replacing the PDF extension with .txt and saving it in TEXT_DIR
    txt_filename = os.path.splitext(filename)[0] + '.txt'
    txt_file_path = os.path.join(TEXT_DIR, txt_filename)

    # Write the text to the file
    with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)

    print(f"Text saved to {txt_file_path}")

def process_airtable_records(view=VIEW_NAME, start_row=START_ROW, end_row=0):
    """Fetches records from a specified Airtable view and processes PDFs starting from a specific row and optionally ending at a specific row."""
    # Fetch records from Airtable using the specified view
    records = table.all(view=view)

    # Determine the actual end row, if 0 or more than available records, process all
    if end_row == 0 or end_row > len(records):
        end_row = len(records)

    # Process records starting from the specified row and ending at the specified row
    for idx, record in enumerate(records[start_row - 1:end_row], start=start_row):
        # Get the PDF attachment field
        pdf_attachments = record['fields'].get(PDF_FIELD_NAME)
        codice_value = record['fields'].get('Codice', f'Row_{idx}')  # Get 'Codice' field value, fallback if missing

        if pdf_attachments:
            for attachment in pdf_attachments:
                pdf_url = attachment['url']
                # Use the 'Codice' value as the filename
                pdf_filename = f"{codice_value}.pdf"
                print(f"Downloading {pdf_filename} from row {idx}...")

                # Download the PDF
                pdf_path = download_pdf(pdf_url, pdf_filename)

                # Extract text from the PDF
                pdf_text = extract_text_from_pdf(pdf_path)

                # Clean the extracted text while preserving entities and structure
                cleaned_text = clean_text_with_preserved_entities(pdf_text)
                final_text = maintain_structure(cleaned_text)

                print(f"Cleaned text from {pdf_filename} (row {idx}):\n{final_text}\n")

                # Save the cleaned text to a .txt file in the text_files directory
                save_text_to_file(pdf_filename, final_text)
        else:
            print(f"No PDF found for record: {record['id']} (row {idx})")


if __name__ == '__main__':
    process_airtable_records(start_row=1, end_row=20)
