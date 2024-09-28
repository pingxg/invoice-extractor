# Invoice Metadata Extractor

This project extracts key information from invoices in PDF format. It utilizes Python, LangChain, OpenAI's GPT-4 API, and Docker for deployment.

## Features

- Extracts key information such as manufacturer, billing company, invoice numbers, contract terms, and more.
- Supports both text-based and image-based PDFs.
- Output is saved as a JSON file / Excel file.

## Requirements

- Python 3.11+
- Docker or Docker Compose

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-repo/invoice-extractor.git
    cd invoice-extractor
    ```

2. Create a `.env` file in the project root and add your OpenAI API key:

    ```bash
    OPENAI_API_KEY=your_openai_api_key
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Build the Docker image:

    ```bash
    docker-compose build
    ```

## Usage

To process PDFs in a folder:

1. Place your PDFs in the `invoices/` folder.
2. Run the script:

    ```bash
    docker-compose up
    ```

3. The extracted data will be saved in `output.json`.

## Debugging

- If you encounter issues with text extraction, ensure the PDF files are accessible and correctly formatted.
- Use `docker-compose logs` to view logs and errors during execution.

## License

This project is open-source under the MIT License.
