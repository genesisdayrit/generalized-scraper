# Generalized Scraper

## Abstract
Generalized Scraper is a Python script designed to retrieve, process, and evaluate HTML content from a specified URL. The script divides the content into chunks, processes these chunks using OpenAI's GPT models, and generates a final evaluation and response. The aim is to automate and streamline the evaluation and processing of HTML content for various purposes.

## Introduction
Generalized Scraper automates the following tasks:
1. Retrieving HTML content from a specified URL.
2. Chunking the HTML content into manageable pieces.
3. Processing each chunk using OpenAI's GPT models.
4. Evaluating and summarizing the processed chunks.
5. Generating a Python script based on the final combined response.

## Environment Variables
The script relies on several environment variables defined in a .env file. An example configuration is provided in a .env.example file:

`.env.example`

```
OPENAI_API_KEY=your_openai_api_key

TARGET_SCHEMA_PROMPT_PATH=path_to_your_target_schema_prompt.txt
CHUNK_EVALUATOR_PATH=path_to_your_chunk_evaluator.txt
PYTHON_SCRIPT_GENERATOR_PATH=path_to_your_python_script_generator.txt
```

## Script Overview

### Dependencies
Generalized Scraper requires the following Python packages:
- python-dotenv
- openai
- selenium
- beautifulsoup4
- tiktoken

These can be installed using pip:

```
pip install -r requirements.txt
```

### Script Components

#### Load Environment Variables
The script starts by loading environment variables using the dotenv package.

#### Setup OpenAI Client
It initializes the OpenAI client using the API key from environment variables.

#### Define Paths to Configuration Files
The paths to necessary configuration files are defined using environment variables.

#### Utility Functions
Generalized Scraper contains several utility functions:
- read_file_content: Reads the content of a file.
- calculate_token_count: Calculates the number of tokens in a text.
- calculate_word_count: Calculates the number of words in a text.
- estimate_memory_size: Estimates the memory size of a text in MB.
- estimate_page_count: Estimates the number of pages based on character count.
- save_to_file: Saves text to a file.
- process_chunks: Processes chunks of text using OpenAI's GPT models.

#### Main Function
The main function performs the following steps:
1. Retrieves HTML content from a specified URL.
2. Parses and prettifies the HTML content using BeautifulSoup.
3. Calculates various metrics (token count, word count, memory size, page count).
4. Divides the content into chunks based on user input.
5. Saves each chunk to a file.
6. Reads system prompts from configuration files.
7. Processes the chunks and generates responses.
8. Concatenates and saves the final response.
9. Evaluates the final response using another prompt.
10. Combines the evaluation summary with the final response and saves it.
11. Generates a Python script based on the combined response.

### Error Handling
Generalized Scraper includes basic error handling for file operations and HTTP requests.

## Usage
1. Configure the environment variables in a .env file based on the provided .env.example.
2. Install the required Python packages.
3. Run the script:

```
python generalized_scraper.py
```

## Conclusion
Generalized Scraper provides an automated solution for processing and evaluating HTML content from a web page. By leveraging OpenAI's GPT models, it can efficiently handle large amounts of text and generate useful insights and scripts based on the processed content. This README outlines the script's functionality and provides guidance on setup and usage. Feedback and suggestions for improvement are welcome.
