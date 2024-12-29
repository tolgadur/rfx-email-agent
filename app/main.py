from app.email_agent_runner import EmailAgentRunner


def main():
    """Entry point of the application."""
    runner = EmailAgentRunner()
    runner.run()


if __name__ == "__main__":
    main()
