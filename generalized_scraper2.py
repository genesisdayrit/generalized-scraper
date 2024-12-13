import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import tiktoken
import datetime
import time
import re

# Load environment variables
load_dotenv()

# Set up OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Define consolidated prompts
CHUNK_EVALUATOR_PROMPT_TEMPLATE = """
You are an expert at webscraping, using BeautifulSoup, and parsing HTML.
You will be given a number of HTML evaluator responses that are searching chunks of a larger HTML document for the following fields:
{target_schema}

Please identify which chunk contains most of the fields and summarize the findings.
"""

PYTHON_SCRIPT_GENERATOR_PROMPT_TEMPLATE = """
You are an expert at generating BeautifulSoup Python scripts.
The target fields for the schema that we are looking to map are:
{target_schema}

Please create a BeautifulSoup Python script that extracts the relevant information from the website given the inspected HTML element field mappings and outputs the results to a JSON file.
Only return the Python script with no other text.

Here is an example of another python script that was used to output to a timestamped json file:
{example_script}

The URL for this script is: {url}
"""

TARGET_SCHEMA_PROMPT_TEMPLATE = """
You are an expert at web scraping, using BeautifulSoup, and parsing HTML.
You will be given a chunk of HTML to analyze. This chunk is part of a larger HTML document.
The goal is to extract the following fields:
{target_schema}

Please inspect the HTML for any signs of the above fields. Return the exact HTML snippet and a surrounding context snippet for each field found.
"""

# Helper functions
def calculate_token_count(text):
    enc = tiktoken.encoding_for_model("gpt-4")
    return len(enc.encode(text))

def save_to_file(text, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

def create_directory_for_domain(url):
    domain = re.sub(r"https?://", "", url).rstrip('/').replace('.', '_')
    directory_path = os.path.join('artifacts', domain)
    os.makedirs(directory_path, exist_ok=True)
    return directory_path

def divide_into_chunks(text, num_chunks):
    chunk_length = len(text) // num_chunks
    return [text[i * chunk_length:(i + 1) * chunk_length] for i in range(num_chunks)]

def read_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        sys.exit(1)

def process_chunks(chunks, prompt_template, target_schema):
    responses = []
    for i, chunk in enumerate(chunks):
        prompt = prompt_template.format(target_schema=target_schema)
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": chunk}
            ]
        )
        responses.append(response.choices[0].message.content)
    return responses

def main():
    # User input for URL and target schema
    url = input("Enter the URL of the website to scrape: ")
    target_schema = input("Enter the target fields you want to scrape, separated by commas: ")

    # Load example script
    example_script_path = "example_bs4_script.txt"
    example_script = read_file_content(example_script_path)

    # Create directory based on domain
    directory_path = create_directory_for_domain(url)

    # Set up Selenium WebDriver
    driver = webdriver.Chrome()
    driver.get(url)

    # Wait for the page to load dynamically
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(5)

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    html_content = soup.prettify()
    driver.quit()

    # Calculate token count and recommended chunks
    token_count = calculate_token_count(html_content)
    recommended_token_chunk_size = 30000
    recommended_chunks = token_count // recommended_token_chunk_size + (1 if token_count % recommended_token_chunk_size > 0 else 0)

    print(f"HTML Content Token Count: {token_count}")
    print(f"Recommended Number of Chunks: {recommended_chunks}")

    # Divide content into chunks
    chunks = divide_into_chunks(html_content, recommended_chunks)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")

    # Save and process chunks
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(directory_path, f"{timestamp}_html_chunk_{i + 1}.html")
        save_to_file(chunk, chunk_filename)

    # Process chunks with the evaluator prompt
    chunk_evaluator_prompt = CHUNK_EVALUATOR_PROMPT_TEMPLATE.format(target_schema=target_schema)
    responses = process_chunks(chunks, CHUNK_EVALUATOR_PROMPT_TEMPLATE, target_schema)

    # Combine responses

    final_response = "\n".join(responses)
    final_filename = os.path.join(directory_path, f"{timestamp}_final_response.txt")
    save_to_file(final_response, final_filename)

    # Generate Python script
    python_script_prompt = PYTHON_SCRIPT_GENERATOR_PROMPT_TEMPLATE.format(target_schema=target_schema, example_script=example_script, url=url)
    python_script_response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[
            {"role": "system", "content": python_script_prompt},
            {"role": "user", "content": final_response}
        ]
    ).choices[0].message.content

    python_script_filename = os.path.join(directory_path, f"{timestamp}_scraping_script.py")
    save_to_file(python_script_response, python_script_filename)
    print(f"Python script saved to {python_script_filename}")

if __name__ == "__main__":
    main()