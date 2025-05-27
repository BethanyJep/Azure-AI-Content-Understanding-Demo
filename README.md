# Azure Receipt Analyzer

This Flask application leverages Azure Content Understanding API to analyze receipts and extract structured data from them, such as merchant information, date, items purchased, prices, totals, and more.

## Features

- Upload and analyze receipt images or PDFs
- View structured data extracted from receipts in a comprehensive tabular format
- Standard receipt fields displayed regardless of receipt content
- Toggle between formatted table view and raw JSON data
- Visual sample receipt gallery with thumbnails
- Built-in PDF viewer for PDF receipts
- Complete field reference guide included
- Supports multiple file formats (PNG, JPG, PDF, etc.)
- Uses Azure Content Understanding API with receipt-analyzer capabilities

## Prerequisites

- Python 3.7 or higher
- Azure subscription with access to Content Understanding API
- Azure Content Understanding resource with receipt-analyzer capability

## Setup

1. Clone this repository:
   ```
   git clone <repository-url>
   cd receipts-content-understanding
   ```

2. Create and activate a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Fill in your Azure Content Understanding API details
   ```
   cp .env.template .env
   # Edit .env with your credentials
   ```

## Azure Content Understanding API Setup

1. Go to the [Azure Portal](https://portal.azure.com)
2. Create a new Content Understanding resource
3. Once created, note down:
   - Endpoint URL
   - API key
   - API version

## Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Upload a receipt image or select one of the sample receipts

## Project Structure

```
├── app.py                 # Main Flask application
├── content_analyzer.py    # Azure Content Understanding API client
├── requirements.txt       # Project dependencies
├── .env.template          # Template for environment variables
├── static/                # Static files (CSS, JS, uploaded images)
│   ├── uploads/           # User uploaded receipts
│   └── samples/           # Sample receipts (symlinks)
├── templates/             # HTML templates
│   ├── base.html          # Base template with layout
│   └── index.html         # Main page template
├── uploads/               # Directory for uploaded files
└── sample-receipts/       # Sample receipt files for testing
```

## Sample Receipt Data

This project includes several sample receipts in the `sample-receipts` directory. These can be used to test the application without having to upload your own receipts.

## Security Considerations

- This application is for demonstration purposes only and may require additional security measures for production use
- Environment variables and API keys should be kept secure
- File uploads should be validated and sanitized
- Implement proper authentication and authorization for production use

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the Azure Content Understanding API for receipt analysis
- Sample receipts provided for demonstration purposes
