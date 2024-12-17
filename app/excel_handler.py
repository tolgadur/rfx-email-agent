import io
import pandas as pd
from email.message import Message
from pinecone_handler import send_message_to_assistant


def extract_excel_from_email(msg: Message):
    try:
        for part in msg.walk():
            if part.get_content_maintype() == "application":
                filename = part.get_filename()
                if filename and (
                    filename.endswith(".xlsx") or filename.endswith(".xls")
                ):
                    payload = part.get_payload(decode=True)
                    excel_file = io.BytesIO(payload)
                    print(f"Successfully extracted Excel file: {filename}")
                    return excel_file, filename
        return None, "No Excel file found in attachment"
    except Exception as e:
        print(f"Error extracting Excel file: {e}")
        return None, f"Error extracting Excel file: {str(e)}"


def process_questions(df: pd.DataFrame):
    """Process questions in DataFrame and get answers."""
    try:
        if "Questions" not in df.columns:
            return None, "No 'Questions' column detected in Excel file"

        if df.empty:
            return None, "Excel file is empty"

        print(f"Processing {len(df)} questions...")

        # Create a copy to avoid modifying the original
        processed_df = df.copy()
        processed_df["Answers"] = processed_df["Questions"].apply(
            lambda q: (send_message_to_assistant(str(q)) if pd.notna(q) else "")
        )

        if processed_df["Answers"].notna().any():
            print("Successfully processed all questions")
            return processed_df, f"Processed {len(df)} questions successfully"
        else:
            return None, "No answers were generated"

    except Exception as e:
        print(f"Error processing questions: {e}")
        return None, f"Error processing questions: {str(e)}"


def process_excel_attachment(msg: Message):
    """Process Excel attachment and handle errors."""
    excel_file, extract_message = extract_excel_from_email(msg)
    if not excel_file:
        return extract_message, None

    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        print("Successfully read Excel file")

        # Process questions
        processed_df, process_message = process_questions(df)
        if processed_df is None:
            print(f"Processing failed: {process_message}")
            return "Could not process Excel file.", None

        # Save updated DataFrame to bytes
        output = io.BytesIO()
        processed_df.to_excel(output, index=False)
        output.seek(0)
        print("Successfully saved processed Excel file")

        return (
            "Excel file processed successfully. "
            f"Processed {len(processed_df)} questions and added answers.",
            output
        )

    except Exception as e:
        error_msg = "Could not process Excel file."
        print(f"Error details: {str(e)}")
        return error_msg, None
