# Email RFP Agent

A smart email agent that automatically processes and responds to RFPs (Request for Proposals) received via email. The agent can handle both plaintext questions in email bodies and attached Excel/CSV files containing RFP questions. It uses RAG (Retrieval Augmented Generation) to provide accurate answers based on your organization's documentation.

## Features

- Monitors a designated email inbox for incoming RFPs
- Processes questions from email body text
- Handles Excel/CSV attachments with RFP questions
- Uses RAG to generate accurate responses based on your documentation
- Supports both local document processing and remote PDF ingestion via URL
- Maintains document embeddings in a PostgreSQL database with pgvector

## Project Structure

```
email-agent/
├── app/
│   ├── main.py              # Entry point: runs email agent and API server
│   ├── api.py               # FastAPI endpoints for document processing
│   ├── email_handler.py     # IMAP polling and SMTP sending
│   ├── excel_handler.py     # Excel file processing
│   ├── document_processor.py # Document processing and embedding
│   ├── embeddings_dao.py    # Database operations for embeddings
│   ├── db_handler.py        # Database connection management
│   ├── rag_service.py       # RAG implementation
│   ├── template_handler.py  # Email template rendering
│   ├── models.py           # SQLAlchemy models
│   ├── data_types.py       # Pydantic models and data classes
│   └── config.py           # Configuration management
├── data/
│   └── docs/               # Directory for source documents
├── assets/
│   └── email.md           # Email response template
├── test/                  # Test files
├── Dockerfile            # Container configuration
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (not in version control)
└── README.md            # Documentation
```

## Adding Documents

There are two ways to add documents to the system:

### 1. Local Document Directory

Place your PDF or Markdown documents in the `data/docs` directory. The system will automatically process these documents on startup. The documents should contain your organization's knowledge base, such as:
- Technical documentation
- Product specifications
- Company policies
- Previous RFP responses

### 2. Remote PDF Processing API

You can also add PDF documents via URL using the HTTP API endpoint:

```bash
curl -X POST "http://localhost:8000/process-pdf-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/document.pdf",
    "password": "your-api-password"
  }'
```

The endpoint will:
- Download the PDF from the provided URL
- Validate it's a valid PDF file
- Process and embed its content
- Store the embeddings in the database

Note: The API is password-protected. Set the `API_PASSWORD` environment variable to secure the endpoint.

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your configuration:
   - Email credentials
   - Database URL
   - API password
   - Other settings
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install system dependencies:
   ```bash
   # On macOS
   brew install libmagic
   
   # On Ubuntu
   apt-get install libmagic1
   ```
5. Run the application:
   ```bash
   python -m app.main
   ```

## Docker Support

Build and run with Docker:

```bash
docker build -t email-agent .
docker run --env-file .env email-agent
```
