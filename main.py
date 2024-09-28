import os
import json
from openai import OpenAI
import openai
import fitz  # PyMuPDF for reading PDF files
from pdf2image import convert_from_path  # For converting PDF pages to images
import base64  # For encoding images to base64
import pandas as pd  # For saving data to Excel
from dotenv import load_dotenv
import requests  # For making requests to GPT-4 API

# Load environment variables from .env file
load_dotenv()

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


# Function to extract text from PDFs using PyMuPDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf_document:
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text("text")
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text


# Function to encode an image as base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Function to extract data from image using GPT-4 Vision
def extract_data_from_image(image_base64):
    prompt = """
    You are given the image of a machine installment payment invoice. Extract the following information as plain json, and ensure to parse all date information into the format yyyy.mm.dd:
    - Manufacturer
    - Billing company
    - Invoice numbers
    - Contract numbers
    - Device names (if any)
    - Address related to the use of this device
    - Contract term
    - Current billing month
    - Total contract term
    - Net price every term

    If there are multiple contract numbers in an invoice, the exported file can have an additional row.
    If there are duplicates in the result, only keep one; if there is only one result, it does not need to be a list.
    no need to output any additonal characters
    all output in english
    """

    # Prepare the request payload for GPT-4 Vision
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    payload = {
        "model": "gpt-4o-mini",  # Use GPT-4 Vision model
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this invoice image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            },
        ],
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    )
    return response.json()


# Function to extract data using LangChain and OpenAI
def extract_data_with_langchain(text):
    prompt = """
    You are given the text of a machine installment payment invoice. Extract the following information as plain json, please remember to parse all the date information to the format of yyyy.mm.dd:
    - Manufacturer
    - Billing company
    - Invoice numbers
    - Contract numbers
    - Device names (if any)
    - Address related to the use of this device
    - Contract term
    - Current billing month
    - Total contract term
    - Net price every term

    If there are multiple contract numbers in an invoice, the exported file can have an additional row.
    If there are duplicates in the result, only keep one; if there is only one result, it does not need to be a list.
    no need to output any additonal characters
    all output in english

    """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
    )
    return completion.choices[0].message


# Main function to process all PDFs in a folder and save as Excel
def process_pdfs_in_folder(folder_path, output_file):
    data = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            print(f"Processing file: {file_path}")

            # Step 1: Attempt to extract text from the PDF using PyMuPDF
            extracted_text = extract_text_from_pdf(file_path)

            if extracted_text.strip():  # If text extraction succeeds
                print(f"Text successfully extracted from {file_path}")
                try:
                    # Here you can process the extracted text with LangChain or GPT
                    extracted_data = extract_data_with_langchain(extracted_text)
                    # Parse the result as JSON and append it
                    json_data = json.loads(
                        extracted_data.content.strip("```json\n").strip("```")
                    )
                    data.append(json_data)
                except Exception as e:
                    print(f"Error processing extracted text: {e}")

            else:
                # Step 2: Fallback to image-based extraction if text extraction fails
                print(
                    f"Text extraction failed, switching to image extraction for {file_path}"
                )
                try:
                    # Convert PDF to images
                    images = convert_from_path(file_path)
                    for i, image in enumerate(images):
                        # Save each image temporarily
                        image_path = f"temp_image_{i}.jpg"
                        image.save(image_path, "JPEG")

                        # Encode image to base64
                        encoded_image = encode_image(image_path)

                        # Extract data from the image using GPT-4 Vision
                        extracted_data = extract_data_from_image(encoded_image)
                        print(f"Extracted Data from page {i + 1}: {extracted_data}")

                        # Parse and append the extracted data
                        try:
                            extracted_json = json.loads(
                                extracted_data["choices"][0]["message"]["content"]
                                .strip("```json\n")
                                .strip("```")
                            )
                            data.append(extracted_json)
                        except Exception as e:
                            print(f"Error parsing GPT-4 response: {e}")

                        # Clean up by removing the temporary image file
                        os.remove(image_path)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    # Convert list of JSON objects to a pandas DataFrame
    if data:
        df = pd.DataFrame(data)
        # Save the DataFrame to an Excel file
        df.to_excel(output_file, index=False)
        print(f"Data successfully saved to {output_file}")
    else:
        print("No data to save.")


# Run the script
if __name__ == "__main__":
    folder_path = "invoices"  # Folder containing PDFs
    output_file = "output.xlsx"  # Output Excel file
    process_pdfs_in_folder(folder_path, output_file)
