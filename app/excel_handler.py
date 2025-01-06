import io
from email.message import Message
from typing import List, Tuple, Dict, Optional
import pandas as pd
from app.rag_service import RAGService, RAGResponse
from app.config import MIN_SIMILARITY_TO_ANSWER


class ExcelHandler:
    """Handles Excel file processing from email attachments."""

    def __init__(self, rag_service: RAGService):
        """Initialize handlers.

        Args:
            rag_service: Service for RAG operations
        """
        self.rag_service = rag_service

    def process_excel_attachment(
        self, msg: Message
    ) -> Tuple[str, Dict[str, io.BytesIO]]:
        """Process all Excel attachments and handle errors."""
        excel_files, skipped_files = self.extract_excel_from_email(msg)

        # Initialize results with skipped files
        results = []
        if skipped_files:
            results.extend(
                f"File '{filename}' was skipped: {reason}"
                for filename, reason in skipped_files
            )

        if not excel_files and not skipped_files:
            return "No attachments found.", {}

        processed_files = {}
        for excel_file, filename in excel_files:
            output, message = self._process_single_excel_file(excel_file, filename)

            if output:
                processed_files[filename] = output
                results.append(f"File '{filename}' processed successfully: {message}")
            else:
                results.append(f"File '{filename}' could not be processed: {message}")

        # Create detailed summary
        detailed_summary = "\n".join(f"- {result}" for result in results)

        return detailed_summary, processed_files

    def extract_excel_from_email(
        self, msg: Message
    ) -> Tuple[List[Tuple[io.BytesIO, str]], List[Tuple[str, str]]]:
        """Extract all Excel files from email attachments."""
        excel_files = []
        skipped_files = []

        try:
            for part in msg.walk():
                if part.get_content_maintype() == "application":
                    filename = part.get_filename()
                    excel_file, skipped = self._process_attachment(part, filename)

                    if excel_file:
                        excel_files.append((excel_file, filename))
                    elif skipped:
                        skipped_files.append(skipped)

            self._log_extraction_results(excel_files, skipped_files)
            return excel_files, skipped_files

        except Exception as e:
            print(f"Error extracting Excel files: {e}")
            return [], []

    def _is_excel_file(self, filename: str) -> bool:
        """Check if a file is an Excel file based on extension."""
        return filename.endswith((".xlsx", ".xls"))

    def _create_skipped_file_entry(self, filename: str) -> Tuple[str, str]:
        """Create a skipped file entry with reason."""
        reason = "Unsupported file format. Only .xlsx and .xls files are supported"
        return filename, reason

    def _create_concatenated_questions(self, df: pd.DataFrame) -> pd.Series:
        """Create concatenated questions from DataFrame rows."""
        return df.apply(
            lambda row: "\n".join(str(val) for val in row if pd.notna(val)), axis=1
        )

    def _get_answers(self, questions: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Get answers for the given questions using RAG."""
        results = [
            self.rag_service.send_message(q) if q else RAGResponse("", None)
            for q in questions
        ]
        answers = [r.text for r in results]
        scores = [r.max_similarity for r in results]
        return pd.Series(answers), pd.Series(scores)

    def _save_processed_dataframe(self, df: pd.DataFrame) -> io.BytesIO:
        """Save processed DataFrame to bytes buffer."""
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output

    def _log_extraction_results(
        self,
        excel_files: List[Tuple[io.BytesIO, str]],
        skipped_files: List[Tuple[str, str]],
    ) -> None:
        """Log the results of file extraction."""
        if not excel_files:
            print("No Excel files found in attachments")
        else:
            print(f"Found {len(excel_files)} Excel files")
            if skipped_files:
                print(f"Skipped {len(skipped_files)} non-Excel files")

    def _process_attachment(
        self, part: Message, filename: str
    ) -> Tuple[Optional[io.BytesIO], Optional[Tuple[str, str]]]:
        """Process a single email attachment.

        Returns:
            Tuple containing either:
            - (BytesIO, None) for Excel files
            - (None, (filename, reason)) for skipped files
        """
        if not filename:
            return None, None

        if self._is_excel_file(filename):
            payload = part.get_payload(decode=True)
            excel_file = io.BytesIO(payload)
            print(f"Found Excel file: {filename}")
            return excel_file, None
        else:
            skipped = self._create_skipped_file_entry(filename)
            print(f"Skipped file {filename}: {skipped[1]}")
            return None, skipped

    def _process_questions(
        self, df: pd.DataFrame
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """Process all columns in DataFrame and get answers."""
        try:
            if df.empty:
                return None, "Excel file is empty"

            print(f"Processing {len(df)} questions...")
            processed_df = df.copy()

            # Process questions and get answers
            questions = self._create_concatenated_questions(processed_df)
            answers, scores = self._get_answers(questions)

            answers = [
                (
                    answer
                    if score is not None and score >= MIN_SIMILARITY_TO_ANSWER
                    else "Not enough information to answer this question."
                )
                for answer, score in zip(answers, scores)
            ]

            processed_df["Answers"] = answers
            processed_df["Similarity Score"] = [
                f"{s * 100:.1f}%" if s is not None and not pd.isna(s) else "N/A"
                for s in scores
            ]

            if processed_df["Answers"].notna().any():
                print("Successfully processed all questions")
                return processed_df, f"Processed {len(df)} questions successfully"

            return None, "No answers were generated"

        except Exception as e:
            print(f"Error processing questions: {e}")
            return None, f"Error processing questions: {str(e)}"

    def _process_single_excel_file(
        self, excel_file: io.BytesIO, filename: str
    ) -> Tuple[Optional[io.BytesIO], str]:
        """Process a single Excel file and return result."""
        try:
            df = pd.read_excel(excel_file)
            print(f"Successfully read {filename}")

            processed_df, process_message = self._process_questions(df)
            if processed_df is None:
                return None, process_message

            output = self._save_processed_dataframe(processed_df)
            return output, process_message

        except Exception as e:
            return None, str(e)
