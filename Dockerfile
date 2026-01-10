# Use the official Microsoft Playwright image as base
# It comes with Python and all necessary system dependencies for browsers
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Add poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* README.md ./

# Install dependencies (without the project itself)
RUN poetry install --no-root --without dev

# Copy source code
COPY src/ ./src/

# Install the project
RUN poetry install --without dev

# Create directory for auth persistence
RUN mkdir -p /root/.pynotebooklm

# Set the entrypoint to the CLI
ENTRYPOINT ["pynotebooklm"]

# Default command
CMD ["--help"]
