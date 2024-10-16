import fitz  # PyMuPDF
import re
import json
import os
import pytesseract
from pdf2image import convert_from_path
import nltk

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required resources for NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Global Variables
PDF_DIRECTORY = '/Users/it/desktop/PDFs'  # Directory containing the PDF files
OUTPUT_DIRECTORY = '/Users/it/desktop/js'  # Directory to save the JSON files

# Initialize lemmatizer and stopword list
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english') + stopwords.words('italian'))  # Add English and Italian stopwords

# Mapping of section names to possible headings
SECTION_NAME_MAPPING = {
    "Finalità": [
        "Finalità", "scopo", "obiettivi", "Ambito"
    ],
    "Descrizione dell’intervento": [
        "Tipo di intervento"
    ],
    "Riferimenti normativi": [
        "Norme di riferimento", "dispositivi normativi"
    ],
    "Dotazione finanziaria": [
        "Dotazione finanziaria"
    ],
    "Interventi ammissibili": [
        "Spese ammissibili"
    ],
    "Beneficiari": [
        "Requisiti di ammissibilità", "a chi si rivolge", "chi può fare domanda"
    ],
    "Obblighi del beneficiario": [
        "Condizioni e obblighi dei beneficiari"
    ],
    "Modalità di presentazione della domanda": [
        "Procedura di richiesta", "come fare domanda"
    ],
    "Termini per la presentazione della domanda": [
        "Scadenze", "date di invio delle domande"
    ],
    "Modalità di erogazione dei fondi": [
        "Tempistiche e modalità di pagamento"
    ],
    "Criteri di selezione": [
        "Modalità di valutazione", "punteggi"
    ],
    "Documentazione richiesta": [
        "Allegati obbligatori", "certificazioni", "dichiarazioni"
    ],
    "Durata del progetto": [
        "Periodo di attuazione", "tempistiche"
    ],
    "Soggetti attuatori": [
        "Chi gestisce il bando", "organizzazioni responsabili"
    ],
    "Vincoli": [
        "Limitazioni", "requisiti particolari", "clausole"
    ],
    "Cofinanziamento": [
        "Percentuale di fondi richiesti", "obblighi di cofinanziamento"
    ],
    "Contatti e supporto": [
        "Informazioni per assistenza", "numeri di riferimento"
    ],
    "Sanzioni e decadenza": [
        "Penalità", "condizioni di revoca"
    ],
    "Stato di avanzamento": [
        "Monitoraggio e valutazione del progetto"
    ],
    "Risultati attesi": [
        "Impatti e obiettivi misurabili"
    ],
    "Oggetto": [
        "Oggetto del Bando", "Oggetto della Gara", "Descrizione dell'Appalto", "Finalità del Bando"
    ],
    "Tipologia di Procedura": [
        "Tipologia di Procedura", "Tipo di Procedura", "Procedura di Gara", "Tipo di Appalto"
    ],
    "Importo a Base di Gara": [
        "Importo a Base di Gara", "Importo Complessivo", "Importo dell'Appalto", "Valore Stimato dell'Appalto"
    ],
    "Durata dell'Appalto": [
        "Durata dell'Appalto", "Durata del Contratto", "Periodo di Esecuzione", "Termine di Esecuzione"
    ],
    "Requisiti di Partecipazione": [
        "Requisiti di Partecipazione", "Condizioni di Partecipazione", "Requisiti per la Partecipazione",
        "Requisiti di Ammissione"
    ],
    "Termine per la Presentazione delle Offerte": [
        "Termine per la Presentazione delle Offerte", "Scadenza per la Presentazione delle Offerte", "Data di Scadenza",
        "Termine di Presentazione"
    ],
    "Modalità di Presentazione delle Offerte": [
        "Modalità di Presentazione delle Offerte", "Modalità di Invio delle Offerte", "Istruzioni per la Presentazione"
    ],
    "Criteri di Aggiudicazione": [
        "Criteri di Aggiudicazione", "Criteri di Valutazione", "Criteri di Scelta dell'Offerta"
    ],
    "Cauzioni e Garanzie Richieste": [
        "Cauzioni e Garanzie Richieste", "Garanzie Richieste", "Cauzioni a Carico dell'Appaltatore"
    ],
    "Informazioni Aggiuntive": [
        "Informazioni Aggiuntive", "Ulteriori Informazioni", "Chiarimenti"
    ],
    "Pubblicazione": [
        "Pubblicazione", "Luogo di Pubblicazione", "Pubblicazione sulla Gazzetta Ufficiale"
    ],

    "Purpose": [
        "Purpose", "Objective", "Scope", "Goals", "Finalità", "scopo", "obiettivi", "Ambito"
    ],
    "Description of the Intervention": [
        "Description of the Intervention", "Type of Intervention", "Descrizione dell’intervento", "Tipo di intervento"
    ],
    "Legal References": [
        "Legal References", "Normative References", "Regulatory References", "Riferimenti normativi", "Norme di riferimento", "dispositivi normativi"
    ],
    "Financial Allocation": [
        "Financial Allocation", "Funding", "Dotazione finanziaria"
    ],
    "Eligible Interventions": [
        "Eligible Expenditures", "Eligible Interventions", "Interventi ammissibili", "Spese ammissibili"
    ],
    "Beneficiaries": [
        "Eligibility Requirements", "Who Can Apply", "Target Audience", "Beneficiaries", "Requisiti di ammissibilità", "a chi si rivolge", "chi può fare domanda"
    ],
    "Beneficiary Obligations": [
        "Beneficiary Obligations", "Conditions and Obligations of Beneficiaries", "Obblighi del beneficiario", "Condizioni e obblighi dei beneficiari"
    ],
    "Application Submission Procedure": [
        "Application Submission Procedure", "How to Apply", "Modalità di presentazione della domanda", "Procedura di richiesta", "come fare domanda"
    ],
    "Application Deadlines": [
        "Application Deadlines", "Submission Deadlines", "Submission Dates", "Termini per la presentazione della domanda", "Scadenze", "date di invio delle domande"
    ],
    "Disbursement of Funds": [
        "Disbursement of Funds", "Payment Timing and Methods", "Modalità di erogazione dei fondi", "Tempistiche e modalità di pagamento"
    ],
    "Selection Criteria": [
        "Selection Criteria", "Evaluation Criteria", "Scoring", "Criteri di selezione", "Modalità di valutazione", "punteggi"
    ],
    "Required Documentation": [
        "Required Documentation", "Mandatory Attachments", "Certificates", "Declarations", "Documentazione richiesta", "Allegati obbligatori", "certificazioni", "dichiarazioni"
    ],
    "Project Duration": [
        "Project Duration", "Implementation Period", "Timelines", "Durata del progetto", "Periodo di attuazione", "tempistiche"
    ],
    "Implementing Bodies": [
        "Implementing Bodies", "Managing Organizations", "Soggetti attuatori", "Chi gestisce il bando", "organizzazioni responsabili"
    ],
    "Constraints": [
        "Constraints", "Special Requirements", "Limitations", "Clauses", "Vincoli", "Limitazioni", "requisiti particolari", "clausole"
    ],
    "Co-financing": [
        "Co-financing", "Percentage of Requested Funds", "Co-financing Obligations", "Cofinanziamento", "Percentuale di fondi richiesti", "obblighi di cofinanziamento"
    ],
    "Contact and Support": [
        "Contact and Support", "Support Information", "Contact Numbers", "Contatti e supporto", "Informazioni per assistenza", "numeri di riferimento"
    ],
    "Penalties and Revocation": [
        "Penalties", "Revocation Conditions", "Penalties and Revocation", "Sanzioni e decadenza", "Penalità", "condizioni di revoca"
    ],
    "Progress Status": [
        "Progress Status", "Project Monitoring and Evaluation", "Stato di avanzamento", "Monitoraggio e valutazione del progetto"
    ],
    "Expected Results": [
        "Expected Results", "Measurable Goals and Impacts", "Risultati attesi", "Impatti e obiettivi misurabili"
    ],
    "Object": [
        "Object", "Subject of the Call", "Subject of the Tender", "Description of the Tender", "Purpose of the Call", "Oggetto", "Oggetto del Bando", "Oggetto della Gara", "Descrizione dell'Appalto", "Finalità del Bando"
    ],
    "Type of Procedure": [
        "Type of Procedure", "Procedure Type", "Tender Procedure", "Contract Type", "Tipologia di Procedura", "Tipo di Procedura", "Procedura di Gara", "Tipo di Appalto"
    ],
    "Contract Base Amount": [
        "Contract Base Amount", "Total Amount", "Contract Value", "Estimated Contract Value", "Importo a Base di Gara", "Importo Complessivo", "Importo dell'Appalto", "Valore Stimato dell'Appalto"
    ],
    "Contract Duration": [
        "Contract Duration", "Contract Period", "Execution Period", "Execution Deadline", "Durata dell'Appalto", "Durata del Contratto", "Periodo di Esecuzione", "Termine di Esecuzione"
    ],
    "Participation Requirements": [
        "Participation Requirements", "Conditions for Participation", "Admission Requirements", "Requisiti di Partecipazione", "Condizioni di Partecipazione", "Requisiti per la Partecipazione", "Requisiti di Ammissione"
    ],
    "Offer Submission Deadline": [
        "Offer Submission Deadline", "Offer Submission Closing Date", "Submission Deadline", "Termine per la Presentazione delle Offerte", "Scadenza per la Presentazione delle Offerte", "Data di Scadenza", "Termine di Presentazione"
    ],
    "Offer Submission Procedure": [
        "Offer Submission Procedure", "Submission Method", "Instructions for Submission", "Modalità di Presentazione delle Offerte", "Modalità di Invio delle Offerte", "Istruzioni per la Presentazione"
    ],
    "Award Criteria": [
        "Award Criteria", "Evaluation Criteria", "Offer Selection Criteria", "Criteri di Aggiudicazione", "Criteri di Valutazione", "Criteri di Scelta dell'Offerta"
    ],
    "Required Guarantees and Bonds": [
        "Required Guarantees", "Required Bonds", "Contractor's Obligations", "Cauzioni e Garanzie Richieste", "Garanzie Richieste", "Cauzioni a Carico dell'Appaltatore"
    ],
    "Additional Information": [
        "Additional Information", "Further Information", "Clarifications", "Informazioni Aggiuntive", "Ulteriori Informazioni", "Chiarimenti"
    ],
    "Publication": [
        "Publication", "Place of Publication", "Publication in the Official Gazette", "Pubblicazione", "Luogo di Pubblicazione", "Pubblicazione sulla Gazzetta Ufficiale"
    ]


}
# Create a regex pattern to match any heading (case-insensitive)
section_pattern = re.compile(r'|'.join(
    [fr'({"|".join(aliases)})' for aliases in SECTION_NAME_MAPPING.values()]),
    re.IGNORECASE
)


# Function to clean and extract important words from text
def clean_text(text):
    # Tokenize using a simple regex to split on non-word characters, but include digits (numbers)
    tokens = re.findall(r'\b\w+\b', text.lower())

    # Remove stopwords, but keep words that are either alphabetic or numeric (like amounts)
    filtered_words = [
        lemmatizer.lemmatize(word) for word in tokens if (word.isalpha() or word.isdigit()) and word not in stop_words
    ]

    return ' '.join(filtered_words)
# Function to extract text from a scanned PDF using OCR
def extract_text_from_scanned_pdf(pdf_path):
    text = ""
    # Convert PDF to images (one image per page)
    images = convert_from_path(pdf_path)
    for image in images:
        # Use Tesseract to extract text from each image
        text += pytesseract.image_to_string(image)
    return text


# Function to extract text from a PDF file (handling both TOC and OCR)
def extract_text_from_pdf(pdf_path):
    text = ""
    toc_found = False  # Flag to detect TOC

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            page_text = page.get_text()

            # If no text is found on the page, it may be a scanned PDF
            if not page_text.strip():
                print(f"No text detected on page {page_num}, applying OCR for {pdf_path}")
                return extract_text_from_scanned_pdf(pdf_path)

            # TOC detection: Skip pages or sections if "Table of Contents" or "Indice" is found
            if re.search(r"(Table of Contents|Indice)", page_text, re.IGNORECASE):
                toc_found = True  # Start skipping TOC pages
                continue

            # Skip TOC-like lines with dots and page numbers (e.g., "Finalità .......... 15")
            if toc_found and re.search(r"\.\s*\d+$", page_text.strip()):
                continue  # Skip this TOC line

            # Check if we're past the TOC by detecting when no page numbers are found
            if toc_found and not re.search(r"\d+\s*$", page_text.strip()):
                toc_found = False  # Likely past the TOC now

            # If not in TOC mode, accumulate the page's text
            text += page_text

    return text


# Function to find which standardized section a heading belongs to
def map_heading_to_section(heading):
    for section_name, possible_headings in SECTION_NAME_MAPPING.items():
        # Check if any of the possible headings are a substring in the current heading
        for possible_heading in possible_headings:
            if re.search(re.escape(possible_heading), heading, re.IGNORECASE):
                return section_name
    return None


# Function to split the text into sections based on headings
def extract_sections(text):
    sections = {}
    current_section_name = None
    current_content = []

    # Split the text by lines
    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # Skip TOC-like lines with page numbers or dots
        if re.search(r'\.\s*\d+$', line):  # E.g., "Finalità .......... 15"
            continue  # Skip this line

        # Check if the line matches any section heading (or combination of words)
        match = section_pattern.search(line)  # Using .search() for partial matches
        if match:
            matched_heading = match.group(0)

            # Map the matched heading (even partial) to the standardized section name
            section_name = map_heading_to_section(line)

            # If we encounter a new section heading, save the previous section
            if current_section_name and current_content:
                # Clean the content of the section
                cleaned_content = clean_text("\n".join(current_content))
                sections[current_section_name] = cleaned_content.strip()

            # Start a new section
            current_section_name = section_name
            current_content = []
        else:
            # If no new heading, keep collecting content for the current section
            if current_section_name:
                current_content.append(line)

    # Don't forget to save the last section
    if current_section_name and current_content:
        cleaned_content = clean_text("\n".join(current_content))
        sections[current_section_name] = cleaned_content.strip()

    return sections


# Function to clean up sections that may contain TOC-like entries
def clean_toc_sections(sections):
    cleaned_sections = {}
    for section_name, content in sections.items():
        # Ignore sections with very short content (likely from TOC)
        if len(content) < 30 and re.search(r'\d+$', content.strip()):
            continue  # Likely a TOC entry, skip it

        # Add to cleaned sections
        cleaned_sections[section_name] = content

    return cleaned_sections


# Function to process a PDF file and save its extracted content as JSON
def process_pdf_to_json(pdf_path, output_dir):
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    # Extract sections based on headings
    sections = extract_sections(text)

    # Clean up TOC-like sections if any remain
    cleaned_sections = clean_toc_sections(sections)

    # Create a dictionary from the sections
    pdf_filename = os.path.basename(pdf_path)
    json_data = {
        "file_name": pdf_filename,
        "sections": cleaned_sections
    }

    # Define output JSON path
    json_filename = os.path.splitext(pdf_filename)[0] + '.json'
    json_output_path = os.path.join(output_dir, json_filename)

    # Save the extracted sections as a JSON file
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    print(f"Processed {pdf_filename}, saved JSON as {json_output_path}")


# Main function to process all PDFs in a directory
def process_pdfs_in_directory(pdf_directory, output_directory):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(pdf_directory):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_directory, filename)
            process_pdf_to_json(pdf_path, output_directory)


# Example usage
if __name__ == "__main__":
    process_pdfs_in_directory(PDF_DIRECTORY, OUTPUT_DIRECTORY)
