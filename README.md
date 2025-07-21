# UniTech Knowledge Assistant

A RAG (Retrieval-Augmented Generation) application built with Streamlit and Snowflake Cortex for intelligent document search and question answering.

## Overview

This application allows users to upload documents and ask questions about them using AI-powered search and generation capabilities. It leverages Snowflake's Cortex Search and various LLM models to provide accurate, context-aware responses.

## Features

- **Document Upload & Processing**: Upload PDF documents that are automatically processed and chunked
- **AI-Powered Search**: Uses Snowflake Cortex Search to find relevant document chunks
- **Multiple LLM Models**: Support for various models including Mixtral, Llama, Arctic, and more
- **Category Filtering**: Filter searches by document categories
- **Chat History**: Maintains conversation context for better responses
- **Document Links**: Provides links to source documents for verification

## Files Description

### `frontend.py`
The main Streamlit application with full functionality including:
- Chat history support
- Document context integration
- Multiple LLM model selection
- Category-based filtering
- Debug mode for development

### `main.sql`
Database setup script that:
- Creates the database and schema structure
- Defines the text chunking function using LangChain
- Sets up document processing tables
- Creates the Cortex Search Service

### `processing_new_docs.sql`
Automated document processing workflow that:
- Sets up streams and tasks for automatic document processing
- Handles document categorization using AI
- Updates document chunks with category information

## Setup Requirements

1. **Snowflake Account** with Cortex features enabled
2. **Python Environment** with required packages:
   - streamlit
   - snowflake-snowpark-python
   - pandas

## Usage

1. Run the SQL scripts to set up your Snowflake environment
2. Upload documents to the `@docs` stage in Snowflake
3. Launch the Streamlit application:
   ```bash
   streamlit run frontend.py
   ```
4. Configure your model and category preferences in the sidebar
5. Start asking questions about your documents!

## Model Options

- mixtral-8x7b
- snowflake-arctic
- mistral-large2
- llama3-8b
- llama3-70b
- reka-flash
- mistral-7b
- llama2-70b-chat
- gemma-7b

## Architecture

The application uses a three-tier architecture:
1. **Data Layer**: Snowflake database with document storage and processing
2. **Processing Layer**: Cortex Search Service for semantic search
3. **Presentation Layer**: Streamlit web interface

## Contributing

Feel free to submit issues and pull requests to improve the application.

## License

This project is open source and available under the MIT License.
