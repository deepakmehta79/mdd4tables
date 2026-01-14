# Contributing to mdd4tables

Thank you for your interest in contributing to mdd4tables! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the behavior
- Expected vs actual behavior
- Your environment (OS, Python version, package versions)
- Minimal code example demonstrating the issue

### Suggesting Enhancements

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Clearly describe the feature and its use case
- Explain why this would be useful to most users

### Pull Requests

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**:
   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow the existing code style
4. **Test your changes**: Run `pytest tests/` and ensure all tests pass
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if applicable

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mdd4tables.git
cd mdd4tables

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev,viz]"

# Run tests
pytest tests/

# Run linter
ruff check mdd4tables/
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and modular
- Add comments for complex logic

## Testing

- Write tests for all new features
- Aim for high test coverage
- Use descriptive test names
- Test edge cases and error conditions

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_basic.py::test_build_and_exists

# Run with coverage
pytest --cov=mdd4tables tests/
```

## Documentation

- Update README.md for user-facing changes
- Update CLAUDE.md for implementation details
- Add examples for new features
- Update VISUALIZATION.md for new visualization methods
- Use clear, concise language

## Commit Messages

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance tasks

Example: `feat: add PyVis interactive visualization support`

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉