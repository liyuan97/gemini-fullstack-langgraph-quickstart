# Gemini Fullstack LangGraph Quickstart - Backend

This backend application has been updated to use **OpenAI GPT models** instead of Gemini for the main LLM operations, while keeping Google Search functionality intact.

## Environment Setup

Create a `.env` file in the backend directory with the following variables:

```env
# OpenAI API Key (required for LLM operations)
OPENAI_API_KEY=your_openai_api_key_here

# Gemini API Key (still required for Google Search functionality)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Model configurations
# QUERY_GENERATOR_MODEL=gpt-4o-mini
# REFLECTION_MODEL=gpt-4o
# ANSWER_MODEL=gpt-4o
# SEARCH_MODEL=gemini-2.0-flash

# Optional: Agent configurations
# NUMBER_OF_INITIAL_QUERIES=3
# MAX_RESEARCH_LOOPS=2
```

## Changes Made

### 🔄 LLM Provider Switch
- **Query Generation**: Now uses `gpt-4o-mini` (was `gemini-2.0-flash`)
- **Reflection**: Now uses `gpt-4o` (was `gemini-2.5-flash-preview-04-17`)
- **Answer Generation**: Now uses `gpt-4o` (was `gemini-2.5-pro-preview-05-06`)

### 🔍 Search Functionality
- **Google Search**: Still uses Gemini API for native Google Search integration
- **Citation Handling**: Unchanged - still provides proper citations and URL resolution

### 📦 Dependencies Updated
- Replaced `langchain-google-genai` with `langchain-openai`
- Replaced `google-genai` with `openai`
- All other dependencies remain the same

## Installation

```bash
# Install dependencies
pip install -e .

# Or using uv (recommended)
uv pip install -e .
```

## Running the Application

```bash
# Using make
make

# Or directly with uv
uv run langgraph dev

# Or with langgraph CLI
langgraph dev
```

## API Keys Required

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/)
2. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/) (needed for search functionality)

## Architecture

The application maintains the same LangGraph workflow:
1. **Query Generation** (OpenAI) → Generate search queries
2. **Web Research** (Gemini + Google Search) → Perform searches
3. **Reflection** (OpenAI) → Analyze results and identify gaps
4. **Answer Generation** (OpenAI) → Create final comprehensive answer

## Models Used

- **gpt-4o-mini**: Fast and cost-effective for query generation
- **gpt-4o**: More capable model for reflection and final answer generation
- **gemini-2.0-flash**: Dedicated model for Google Search integration (configurable via SEARCH_MODEL)

## Development

```bash
# Run tests
make test

# Format code
make format

# Lint code
make lint
``` 