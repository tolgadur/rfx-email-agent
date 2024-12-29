from app.containers import Container
from app.email_agent_runner import EmailAgentRunner


def main():
    """Entry point of the application."""
    container = Container()
    container.wire(modules=["app.email_agent_runner"])

    runner = EmailAgentRunner()
    runner.run()


if __name__ == "__main__":
    main()
