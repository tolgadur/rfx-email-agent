import io
from typing import List, Tuple, Dict, Optional
import pandas as pd
from email.message import Message
from app.pinecone_handler import send_message_to_assistant


def is_excel_file(filename: str) -> bool:
    """Check if a file is an Excel file based on extension."""
    return filename.endswith((".xlsx", ".xls"))


def create_skipped_file_entry(filename: str) -> Tuple[str, str]:
    """Create a skipped file entry with reason."""
    reason = "Unsupported file format. Only .xlsx and .xls files are supported"
    return filename, reason


def process_attachment(
    part: Message, filename: str
) -> Tuple[Optional[io.BytesIO], Optional[Tuple[str, str]]]:
    """Process a single email attachment.

    Returns:
        Tuple containing either:
        - (BytesIO, None) for Excel files
        - (None, (filename, reason)) for skipped files
    """
    if not filename:
        return None, None

    if is_excel_file(filename):
        payload = part.get_payload(decode=True)
        excel_file = io.BytesIO(payload)
        print(f"Found Excel file: {filename}")
        return excel_file, None
    else:
        skipped = create_skipped_file_entry(filename)
        print(f"Skipped file {filename}: {skipped[1]}")
        return None, skipped


def extract_excel_from_email(
    msg: Message,
) -> Tuple[List[Tuple[io.BytesIO, str]], List[Tuple[str, str]]]:
    """Extract all Excel files from email attachments."""
    excel_files = []
    skipped_files = []

    try:
        for part in msg.walk():
            if part.get_content_maintype() == "application":
                filename = part.get_filename()
                excel_file, skipped = process_attachment(part, filename)

                if excel_file:
                    excel_files.append((excel_file, filename))
                elif skipped:
                    skipped_files.append(skipped)

        log_extraction_results(excel_files, skipped_files)
        return excel_files, skipped_files

    except Exception as e:
        print(f"Error extracting Excel files: {e}")
        return [], []


def log_extraction_results(
    excel_files: List[Tuple[io.BytesIO, str]], skipped_files: List[Tuple[str, str]]
) -> None:
    """Log the results of file extraction."""
    if not excel_files:
        print("No Excel files found in attachments")
    else:
        print(f"Found {len(excel_files)} Excel files")
        if skipped_files:
            print(f"Skipped {len(skipped_files)} non-Excel files")


def create_concatenated_questions(df: pd.DataFrame) -> pd.Series:
    """Create concatenated questions from DataFrame rows."""
    return df.apply(
        lambda row: "\n".join(str(val) for val in row if pd.notna(val)), axis=1
    )


def get_answers(questions: pd.Series) -> pd.Series:
    """Get answers for the given questions using the assistant."""
    return questions.apply(lambda q: send_message_to_assistant(q) if q else "")


def process_questions(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], str]:
    """Process all columns in DataFrame and get answers."""
    try:
        if df.empty:
            return None, "Excel file is empty"

        print(f"Processing {len(df)} questions...")
        processed_df = df.copy()

        # Process questions and get answers
        questions = create_concatenated_questions(processed_df)
        processed_df["Answers"] = get_answers(questions)

        if processed_df["Answers"].notna().any():
            print("Successfully processed all questions")
            return processed_df, f"Processed {len(df)} questions successfully"

        return None, "No answers were generated"

    except Exception as e:
        print(f"Error processing questions: {e}")
        return None, f"Error processing questions: {str(e)}"


def save_processed_dataframe(df: pd.DataFrame) -> io.BytesIO:
    """Save processed DataFrame to bytes buffer."""
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output


def process_single_excel_file(
    excel_file: io.BytesIO, filename: str
) -> Tuple[Optional[io.BytesIO], str]:
    """Process a single Excel file and return result."""
    try:
        df = pd.read_excel(excel_file)
        print(f"Successfully read {filename}")

        processed_df, process_message = process_questions(df)
        if processed_df is None:
            return None, process_message

        output = save_processed_dataframe(processed_df)
        return output, process_message

    except Exception as e:
        return None, str(e)


def create_summary_message(
    total_files: int,
    success_count: int,
    failed_count: int,
    skipped_count: int,
    results: List[str],
) -> str:
    """Create a summary message of processing results."""
    if total_files == 0:
        return "No files were found in the email."

    return (
        f"Found {total_files} attachment(s):\n"
        f"- Successfully processed: {success_count}\n"
        f"- Failed to process: {failed_count}\n"
        f"- Skipped (non-Excel): {skipped_count}\n\n"
        "Detailed results:\n" + "\n".join(results)
    )


def process_excel_attachment(msg: Message) -> Tuple[str, Dict[str, io.BytesIO]]:
    """Process all Excel attachments and handle errors."""
    excel_files, skipped_files = extract_excel_from_email(msg)

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
        output, message = process_single_excel_file(excel_file, filename)

        if output:
            processed_files[filename] = output
            results.append(f"File '{filename}' processed successfully: {message}")
        else:
            results.append(f"File '{filename}' could not be processed: {message}")

    # Create detailed summary
    detailed_summary = "\n".join(f"- {result}" for result in results)

    return detailed_summary, processed_files
