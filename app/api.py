from fastapi import FastAPI, HTTPException
import requests
import magic
import tempfile
from pathlib import Path
from app.document_processor import DocumentProcessor
from app.embeddings_dao import EmbeddingsDAO
from app.data_types import PDFUrlRequest
from app.config import API_PASSWORD

app = FastAPI()


@app.post("/process-pdf-url")
async def process_pdf_url(request: PDFUrlRequest):
    """Process a PDF from a given URL."""
    # Validate password
    if request.password != API_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")

    try:
        # Download the file
        response = requests.get(str(request.url))
        response.raise_for_status()

        # Verify content is PDF before saving
        content = response.content
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        if not file_type.lower() == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="The provided URL does not point to a valid PDF file",
            )

        # Save verified PDF content to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        # Process the PDF using DocumentProcessor
        pdf_path = Path(temp_path)
        document_processor = app.state.document_processor
        document_processor.process_pdf(pdf_path, url=str(request.url))

        # Clean up
        pdf_path.unlink()

        return {"message": "PDF processed successfully"}

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download PDF: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


def init_app(embeddings_dao: EmbeddingsDAO) -> FastAPI:
    """Initialize the FastAPI application with required dependencies."""
    app.state.document_processor = DocumentProcessor(embeddings_dao)
    return app
