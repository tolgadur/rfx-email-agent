# Project structure

email-agent/
├── app/
│ ├── main.py # Entry point: main polling script
│ ├── email_handler.py # Functions for IMAP polling and SMTP sending
│ ├── config.py # Configuration management (e.g., secrets)
│ └── utils.py # Utility functions (e.g., parsing, formatting)
├── Dockerfile # Dockerfile for containerization
├── requirements.txt # Python dependencies
├── .env # Environment variables for secrets (not checked into version control)
└── README.md # Documentation
