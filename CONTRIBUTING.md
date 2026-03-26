# Contributing to Auto-Clip Bot V2

Thank you for your interest in contributing to Auto-Clip Bot V2! We welcome bug reports, feature requests, and code contributions.

## Development Environment Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/auto-clip-bot.git
    cd auto-clip-bot
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r content-bot/requirements.txt
    ```

4.  **Configure API Keys**:
    Copy the sample environment file and add your `CHUTES_API_KEY`.
    ```bash
    cp .env.example .env
    ```

## Running Tests

All tests must pass before submitting a pull request. We use a custom test runner script to ensure dependencies are properly mocked for CI environments.

Run the test suite using this exact command from the root of the repository:
```bash
PYTHONPATH=content-bot python3 content-bot/run_tests.py
```

## Code Guidelines

*   **Security First**: Review `.jules/sentinel.md` for our security principles. Ensure all FFmpeg shell commands are properly sanitized to prevent injection attacks and use timeouts to prevent hangs.
*   **Performance Optimization**: Review `.jules/bolt.md` for optimization patterns. Pay special attention to loop efficiency and limiting unnecessary I/O or external API calls.
*   **Documentation Architecture**: We strictly follow the Divio Documentation System. Ensure documentation is placed correctly as a Tutorial, How-to Guide, Reference, or Explanation. Do not mix concepts in a single file. Ensure all new features are fully documented and code examples run properly.

## Pull Requests

1.  **Open an issue**: If you are planning a major change, please open an issue first to discuss it.
2.  **Create a branch**: Use a descriptive branch name.
3.  **Submit**: Ensure all tests pass and documentation is updated before requesting a review.