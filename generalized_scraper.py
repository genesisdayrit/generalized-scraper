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

# Define paths to the .txt files using environment variables
config = {
    "system_prompt_path": os.getenv('TARGET_SCHEMA_PROMPT_PATH'),
    "chunk_evaluator_path": os.getenv('CHUNK_EVALUATOR_PATH'),
    "python_script_generator_path": os.getenv('PYTHON_SCRIPT_GENERATOR_PATH')
}

def read_file_content(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"An error occurred: {e}"

def calculate_token_count(text):
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = enc.encode(text)
    return len(tokens)

def calculate_word_count(text):
    words = text.split()
    return len(words)

def estimate_memory_size(text):
    size_in_bytes = sys.getsizeof(text)
    size_in_mb = size_in_bytes / (1024 * 1024)  # Convert bytes to MB
    return size_in_mb

def estimate_page_count(char_count):
    characters_per_word = 5.5
    total_words = char_count / characters_per_word
    words_per_page = 500
    total_pages = total_words / words_per_page
    return total_pages

def save_to_file(text, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

def create_directory_for_domain(url):
    # Remove protocol (http://, https://) and trailing slash
    domain = re.sub(r"https?://", "", url)
    domain = domain.rstrip('/')

    # Replace special characters with underscores
    domain = re.sub(r'\W+', '_', domain)

    # Create directory path
    directory_path = os.path.join('artifacts', domain)
    os.makedirs(directory_path, exist_ok=True)
    
    return directory_path

def process_chunks(chunks, system_prompt):
    responses = []
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        chunk_number = i + 1
        prompt = f"HTML evaluator for Chunk {chunk_number} of {total_chunks}\n\n{chunk}"
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        openai_response = completion.choices[0].message.content
        responses.append(openai_response)
    return responses

def main():
    url = input("Enter the URL of the website to scrape: ")

    # Create directory based on the domain
    directory_path = create_directory_for_domain(url)

    # Set up Selenium WebDriver
    driver = webdriver.Chrome()
    driver.get(url)
    
    # Wait for the page to load dynamically and sleep for designated seconds
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(5)

    # Get the page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    html_content = soup.prettify()

    # Close the browser
    driver.quit()

    # Calculate various metrics
    token_count = calculate_token_count(html_content)
    word_count = calculate_word_count(html_content)
    memory_size_mb = estimate_memory_size(html_content)
    char_count = len(html_content)
    page_count = estimate_page_count(char_count)

    print(f"HTML Content Length: {char_count} characters")
    print(f"Estimated Token Count: {token_count}")
    print(f"Word Count: {word_count}")
    print(f"Estimated Memory Size: {memory_size_mb:.2f} MB")
    print(f"Estimated Google Docs Page Count: {page_count:.2f} pages")

    max_token_context_length = 128000
    recommended_token_chunk_size = 30000

    min_chunks = token_count // max_token_context_length + (1 if token_count % max_token_context_length > 0 else 0)
    recommended_chunks = token_count // recommended_token_chunk_size + (1 if token_count % recommended_token_chunk_size > 0 else 0)

    print(f"\nMinimum number of chunks based on maximum token context length ({max_token_context_length} tokens): {min_chunks}")
    print(f"Recommended number of chunks for optimal processing (~{recommended_token_chunk_size} tokens each): {recommended_chunks}\n")

    num_chunks = int(input("Enter the number of chunks you want to create: "))

    chunk_length = char_count // num_chunks
    remainder = char_count % num_chunks

    chunks = []
    for i in range(num_chunks):
        start = i * chunk_length
        if i == num_chunks - 1:
            end = start + chunk_length + remainder
        else:
            end = start + chunk_length
        chunks.append(html_content[start:end])

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")

    # Save and output the chunks
    for i, chunk in enumerate(chunks):
        chunk_filename = os.path.join(directory_path, f"{timestamp}_html_chunk_{i + 1}.html")
        save_to_file(chunk, chunk_filename)
        print(f"Saved chunk {i + 1} to {chunk_filename}")

    system_prompt = read_file_content(config["system_prompt_path"])

    responses = process_chunks(chunks, system_prompt)

    final_response = "\n".join(responses)
    final_filename = os.path.join(directory_path, f"{timestamp}_final_response.txt")
    save_to_file(final_response, final_filename)
    print(f"Final concatenated response saved to {final_filename}")

    # Pass the concatenated response through the chunk evaluator
    chunk_evaluator_prompt = read_file_content(config["chunk_evaluator_path"])

    evaluation_completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[
            {"role": "system", "content": chunk_evaluator_prompt},
            {"role": "user", "content": final_response}
        ]
    )
    evaluation_response = evaluation_completion.choices[0].message.content
    evaluation_filename = os.path.join(directory_path, f"{timestamp}_evaluation_summary.txt")
    save_to_file(evaluation_response, evaluation_filename)
    print(f"Evaluation summary saved to {evaluation_filename}")

    # Concatenate final_response with evaluation summary
    combined_response = f"Final Responses:\n{final_response}\n\nEvaluation Summary:\n{evaluation_response}"
    combined_filename = os.path.join(directory_path, f"{timestamp}_combined_response.txt")
    save_to_file(combined_response, combined_filename)
    print(f"Combined response saved to {combined_filename}")

    # Pass the combined response through the Python script generator
    python_script_generator_prompt = read_file_content(config["python_script_generator_path"])

    python_script_completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[
            {"role": "system", "content": python_script_generator_prompt},
            {"role": "user", "content": f"URL: {url}\n\nCombined Response:\n{combined_response}"}
        ]
    )
    python_script_response = python_script_completion.choices[0].message.content
    python_script_filename = os.path.join(directory_path, f"{timestamp}_scraping_script.py")
    save_to_file(python_script_response, python_script_filename)
    print(f"Python script saved to {python_script_filename}")

if __name__ == "__main__":
    main()
