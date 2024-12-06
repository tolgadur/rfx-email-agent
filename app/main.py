from app.email_handler import fetch_emails, send_email_response

def main():
    for sender, subject, body in fetch_emails():
        print(f"Processing email from {sender}: {subject}")
        
        # Example response logic
        response_body = f"Hello,\n\nYou asked: {body}\n\nHere is your automated response!"
        send_email_response(to_email=sender, subject=subject, body=response_body)

if __name__ == "__main__":
    main()
