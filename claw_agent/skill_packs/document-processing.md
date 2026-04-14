# Document Processing Skill Pack

## PDF Operations
- **Reading**: PyMuPDF (fitz) for text extraction, pdfplumber for tables, OCR fallback for scanned docs
- **Creating**: ReportLab for programmatic, weasyprint for HTML→PDF, LaTeX for academic
- **Merging/Splitting**: PyPDF2 for simple ops. Preserve bookmarks and metadata
- **Forms**: Fill with PyPDF2 or pdfrw. Flatten for read-only distribution
- **Security**: Encrypt with AES-256. Remove metadata before sharing sensitive docs

## Word Documents (.docx)
- python-docx for creation and editing. Preserve styles, headers, footers
- Template-based: Create master template with styles, populate programmatically
- Tables: python-docx Table objects. Merge cells, style consistently
- Images: Inline pictures with proper sizing. EMUs for precise positioning

## Spreadsheets (.xlsx)
- openpyxl for reading/writing. xlsxwriter for high-performance creation
- Formulas: Preserve when editing. Use named ranges for maintainability
- Charts: Create via openpyxl. Bar, line, pie, scatter. Themed consistently
- Large files: Read in streaming mode (read_only=True). Write with constant memory

## Presentations (.pptx)
- python-pptx for creation and editing. Slide layouts from master
- Content hierarchy: Title → Subtitle → Bullet points. One idea per slide
- Images and charts: Proper positioning with EMU coordinates
- Speaker notes: Include in generated decks for presenter reference

## Data Extraction
- **Structured text**: Regex for patterns, then validate with schema
- **Tables**: Camelot/pdfplumber for PDF tables, pandas.read_html for web tables
- **OCR**: Tesseract for on-device, cloud OCR (Google Vision, AWS Textract) for accuracy
- **Invoices/Receipts**: Extract vendor, date, amount, line items. Standardize format
