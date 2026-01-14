**# 📄 Free OCR Web Application**



A production-ready, free OCR web application that converts scanned PDFs and images to editable documents (TXT, DOCX, XLSX) with preserved formatting.



\## ✨ Features



\- \*\*Multi-format Support\*\*: Upload PDFs (including scanned), PNG, JPG, JPEG, TIFF, BMP

\- \*\*Batch Processing\*\*: Process multiple documents (up to 50 pages total)

\- \*\*Multilingual OCR\*\*: Support for 11+ languages (English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Arabic, Hindi)

\- \*\*Smart Output Formats\*\*:

&nbsp; - \*\*TXT\*\*: Clean text with preserved paragraphs

&nbsp; - \*\*DOCX\*\*: Word documents with headings, spacing, and tables

&nbsp; - \*\*XLSX\*\*: Excel spreadsheets with detected tables

\- \*\*Layout Preservation\*\*: Maintains document structure, not just raw text

\- \*\*Table Detection\*\*: Automatically detects and extracts tables

\- \*\*Rate Limiting\*\*: Built-in protection against abuse

\- \*\*Logging System\*\*: Comprehensive logging for debugging and monitoring

\- \*\*Environment Configuration\*\*: Easy configuration via .env file

\- \*\*Free \& Secure\*\*: No paid APIs, files auto-deleted after 1 hour

\- \*\*Modern UI\*\*: Clean, responsive interface with drag-and-drop

\- \*\*Production Ready\*\*: Rate limiting, logging, error handling, health checks



**## 🏗️ Project Structure**



```

ocr\_web\_app/

│

├── app.py                 # Flask main application

├── ocr/                   # OCR processing module

│   ├── \_\_init\_\_.py

│   ├── ocr\_engine.py     # Core OCR logic

│   ├── preprocess.py     # Image preprocessing

│   └── layout\_parser.py  # Layout \& table detection

│

├── templates/

│   └── index.html        # Frontend HTML

├── static/

│   ├── style.css         # Styling

│   └── script.js         # Frontend logic

│

├── uploads/              # Temporary upload storage

├── outputs/              # Temporary output storage

│

├── requirements.txt      # Python dependencies

└── README.md            # This file

```



\## 🚀 Local Setup



\### Prerequisites



1\. \*\*Python 3.8+\*\*

2\. \*\*Tesseract OCR\*\* (required!)

3\. \*\*Poppler\*\* (for PDF conversion)



\### Installing Tesseract



\#### Windows

1\. Download installer: https://github.com/UB-Mannheim/tesseract/wiki

2\. Install to `C:\\Program Files\\Tesseract-OCR\\` # for window users

3\. Add to PATH or set `TESSERACT\_PATH` environment variable



\#### Linux (Ubuntu/Debian)

```bash

sudo apt update

sudo apt install tesseract-ocr

sudo apt install poppler-utils

```



\#### macOS

```bash

brew install tesseract

brew install poppler

```



\### Installation Steps



1\. \*\*Clone/Download the project\*\*

```bash

cd ocr\_web\_app

```



2\. \*\*Create virtual environment\*\*

```bash

python -m venv venv



\# Windows

venv\\Scripts\\activate



\# Linux/Mac

source venv/bin/activate

```



3\. \*\*Install dependencies\*\*

```bash

pip install -r requirements.txt

```



4\. \*\*Configure environment variables\*\*

```bash

\# Copy example config

cp .env.example .env



\# Edit .env with your settings

nano .env  # or use your favorite editor

```




5\. \*\*Run the application\*\*

```bash

python app.py

```



6\. \*\*Open browser\*\*

```

http://localhost:5000

```

\## 🔧 How It Works

\### OCR Pipeline

1\. \*\*File Upload\*\*: User uploads PDF/image files

2\. \*\*Conversion\*\*: PDFs converted to images at 300 DPI

3\. \*\*Preprocessing\*\*:

&nbsp;  - Grayscale conversion

&nbsp;  - Noise removal

&nbsp;  - Adaptive thresholding

&nbsp;  - Auto-deskewing

4\. \*\*OCR Processing\*\*:

&nbsp;  - Tesseract extracts text with layout info

&nbsp;  - Page segmentation mode (PSM) 6 for uniform blocks

5\. \*\*Layout Analysis\*\*:

&nbsp;  - Text blocks identified

&nbsp;  - Tables detected using contour analysis

&nbsp;  - Hierarchical structure preserved

6\. \*\*Output Generation\*\*:

&nbsp;  - TXT: Clean paragraphs with line breaks

&nbsp;  - DOCX: Headings, spacing, tables recreated

&nbsp;  - XLSX: Tables as proper rows/columns


\### Table Detection
Uses OpenCV to detect tables:
1\. Detect horizontal and vertical lines
2\. Find intersections (table cells)
3\. Extract text from each cell
4\. Organize into rows and columns

\### Limitations
\- \*\*Complex Layouts\*\*: Very complex multi-column layouts may not be perfectly preserved
\- \*\*Handwriting\*\*: Tesseract works best with printed text
\- \*\*Image Quality\*\*: Low-quality scans may produce poor results
\- \*\*Table Accuracy\*\*: Complex tables (merged cells, nested tables) may not extract perfectly



\## 📝 Usage Tips
1\. \*\*Better Results\*\*:
&nbsp;  - Use high-quality scans (300 DPI or higher)
&nbsp;  - Ensure good contrast between text and background
&nbsp;  - Straighten skewed documents before scanning



2\. \*\*Language Selection\*\*:
&nbsp;  - Select the correct language before processing
&nbsp;  - Make sure the language pack is installed in Tesseract
&nbsp;  - For mixed-language documents, use the primary language



3\. \*\*Format Selection\*\*:
&nbsp;  - Use \*\*TXT\*\* for simple text extraction
&nbsp;  - Use \*\*DOCX\*\* when you need formatting and structure
&nbsp;  - Use \*\*XLSX\*\* when document contains primarily tables



4\. \*\*Batch Processing\*\*:
&nbsp;  - You can upload multiple files at once
&nbsp;  - Maximum 50 pages total across all files
&nbsp;  - Each file max 50MB


5\. \*\*Performance\*\*:
&nbsp;  - Processing time shown for each document
&nbsp;  - Larger files and higher page counts take longer
&nbsp;  - Rate limits apply: 10 requests/minute, 100/hour per IP



\## 🛡️ Security
\- \*\*File Validation\*\*: Only allowed extensions accepted
\- \*\*Secure Filenames\*\*: All filenames sanitized
\- \*\*Rate Limiting\*\*: Protection against abuse (10 req/min, 100 req/hour)
\- \*\*Auto Cleanup\*\*: Files deleted after 1 hour
\- \*\*No Storage\*\*: No permanent file storage
\- \*\*No User Accounts\*\*: No login required, completely anonymous
\- \*\*Logging\*\*: All actions logged for monitoring
\- \*\*Environment Variables\*\*: Sensitive config stored securely



\## 🐛 Troubleshooting
\### "Tesseract not found"
\- Install Tesseract
\- Set `TESSERACT\_PATH` environment variable



\### "PDF conversion failed"
\- Install Poppler 
\- Check PDF is not password-protected



\### Poor OCR quality

\- Increase scan DPI (300+ recommended)
\- Improve image contrast
\- Remove noise/artifacts from image



\### "Too many pages" error
\- Limit is 50 pages total
\- Split large documents



\### Rate limit errors
\- Wait 1 minute between requests
\- Maximum 100 requests per hour per IP
\- Disable in development: `RATE\_LIMIT\_ENABLED=false`



\### Language not working
\- Install required language pack (see Configuration Guide)
\- Check language code is correct
\- Verify `.traineddata` file exists in tessdata folder



\## 📦 Dependencies
\- \*\*Flask\*\*: Web framework
\- \*\*python-dotenv\*\*: Environment variable management
\- \*\*Tesseract\*\*: OCR engine
\- \*\*pdf2image\*\*: PDF to image conversion
\- \*\*OpenCV\*\*: Image processing \& table detection
\- \*\*Pillow\*\*: Image manipulation
\- \*\*python-docx\*\*: Word document generation
\- \*\*pandas/openpyxl\*\*: Excel file generation



\## 🤝 Contributing

This is an open-source project developed by me Mike Sanga. Feel free to:
\- Report bugs to my email -mykiie85@gmail.com
\- Suggest features
\- Submit pull requests
\- Improve documentation



\## 📄 License
Free to use for personal and  not commercial projects.



\## 🙏 Credits
\- Tesseract OCR by Google
\- Flask web framework
\- OpenCV computer vision library



---


