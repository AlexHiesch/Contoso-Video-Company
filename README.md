![Contoso Video Company](src/contoso.png) 
# Contoso Movie Search Demo (Azure AI Search + Ollama)

![Contoso Video Company](src/contoso.gif) 

This project demonstrates building a movie search application using Azure AI Search combined with local embeddings generated by Ollama. Users can search a movie dataset using various methods:

* **Keyword Search:** Traditional text search using BM25 relevance scoring.
* **Vector Search:** Finds movies based on semantic similarity using embeddings generated from movie metadata (title, overview, tagline, genres).
* **Hybrid Search:** Combines results from both Keyword and Vector search using Reciprocal Rank Fusion (RRF) for a balanced approach.
* **Semantic Search:** Enhances Keyword search by using Microsoft's deep learning models to re-rank results for semantic relevance and extract meaningful captions.

## Features

* **Multiple Search Modes:** Keyword, Vector, Hybrid, and Semantic search.
* **Local Embeddings:** Uses Ollama running locally to generate embeddings (specifically `nomic-embed-text` in the current configuration).
* **Azure AI Search Integration:** Leverages Azure AI Search for indexing, storing embeddings, and performing all search types.
* **Streamlit UI:** A simple web interface built with Streamlit for interacting with the search engine.
* **Infrastructure as Code:** Uses Azure Bicep (`iac/`) to define and deploy the required Azure AI Search resource.
* **Data Processing Notebook:** Includes a Jupyter notebook (`notebooks/1_data_processing.ipynb`) to process the movie data, generate embeddings, and upload them to Azure AI Search.
* **Search Testing Notebook:** Includes a Jupyter notebook (`notebooks/2_search_testing.ipynb`) for programmatically testing search queries.

## Technology Stack

* **Frontend:** Streamlit
* **Backend/Search:** Azure AI Search
* **Embeddings:** Ollama (running `nomic-embed-text` model locally)
* **Programming Language:** Python
* **Infrastructure:** Azure Bicep, Azure CLI
* **Core Libraries:** `azure-search-documents`, `requests`, `pandas`, `python-dotenv`, `streamlit`

## Prerequisites

* **Kaggle Movie Data Set:** https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset
* **Python:** Version 3.10 or higher recommended.
* **Package Manager:** `pip` and `venv` (usually included with Python).
* **Ollama:** Install Ollama locally. Follow instructions at [https://ollama.com/](https://ollama.com/).
    * You will specifically need the `nomic-embed-text` model.
* **Azure CLI:** Install the Azure Command-Line Interface. [Installation Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
* **Azure Subscription:** An active Azure subscription.
* **(Optional) Homebrew:** Required by the `iac/install.sh` script if running on macOS to install Ollama.
* **(Optional) Git:** For cloning the repository.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install and Run Ollama Model:**
    * Ensure Ollama is installed (see Prerequisites).
    * Pull the required embedding model (the project uses `nomic-embed-text` based on `.env` and scripts):
        ```bash
        ollama pull nomic-embed-text
        ```
    * Serve the model (run this in a separate terminal and keep it running):
        ```bash
        ollama serve nomic-embed-text
        ```
        *Note: The `iac/install.sh` script mentions `bge-m3`. If you prefer that model, ensure you update `OLLAMA_MODEL` and `VECTOR_DIMENSION` in your `.env` file and the notebooks accordingly.*

5.  **Deploy Azure Infrastructure:**
    * Log in to Azure:
        ```bash
        az login
        ```
    * (Optional) Set your desired subscription:
        ```bash
        az account set --subscription "YOUR_SUBSCRIPTION_ID_OR_NAME"
        ```
    * Navigate to the `iac` directory:
        ```bash
        cd iac
        ```
    * **Important:** Review and modify the parameters in `install.sh` (like `RG_NAME`, `LOCATION`, `SEARCH_SVC_NAME`, `SEARCH_SKU`) to suit your needs. The default SKU is `basic`. The `free` tier has limitations (e.g., fewer indexes, smaller size) but can be used for testing. Semantic Search requires `basic` or higher.
    * Run the installation script:
        ```bash
        bash install.sh
        ```
    * **Note:** This script will create a Resource Group and an Azure AI Search service. It will output the Search Service Name and the Primary Admin Key. **Copy these values** - you'll need them for the next step.

6.  **Configure Environment Variables:**
    * Create a `.env` file in the project root directory (this file is ignored by Git). You can copy/rename `.env.example` if one exists, or create it from scratch.
    * Add the following variables, replacing placeholders with your actual values:
        ```dotenv
        # .env file

        # --- Data Processing ---
        # Adjust path relative to the `notebooks` directory where the script runs
        SOURCE_FILE_PATH="../data/raw/kaggle_movie_dataset/movies_metadata.csv"
        OUTPUT_PATH="../data/processed/" # Where the backup .jsonl file will be saved

        # --- Ollama Configuration ---
        # Ensure this matches the endpoint where `ollama serve` is listening
        # Note: Processing/App use /api/embed, Test Notebook uses /api/embeddings
        OLLAMA_ENDPOINT="http://localhost:11434/api/embed"
        OLLAMA_MODEL="nomic-embed-text" # Should match the model you pulled/served
        OLLAMA_BATCH_SIZE=32           # Batch size for embedding generation (adjust based on RAM)
        VECTOR_DIMENSION="768"         # Dimension for nomic-embed-text

        # --- Azure AI Search Configuration ---
        # Get these from the output of 'iac/install.sh' or Azure portal
        AZURE_SEARCH_SERVICE_ENDPOINT="https://YOUR_SEARCH_SERVICE_NAME.search.windows.net"
        AZURE_SEARCH_API_KEY="YOUR_PRIMARY_ADMIN_KEY"

        # Choose a name for your index (the data processing script will create it)
        AZURE_SEARCH_INDEX_NAME="contosomovies-nomic-768-idx" # Example name

        # Name for the semantic configuration (must exist in your Azure Search service)
        # Create this manually in the Azure Portal for your index OR use the default one if available
        AZURE_SEMANTIC_CONFIGURATION_NAME="default" # Or your custom config name
        ```
    * **Semantic Configuration:** For "Semantic" search mode to work, you need to:
        * Use a `basic` or higher SKU for Azure AI Search.
        * Enable Semantic Search on your service tier in the Azure Portal.
        * Create a Semantic Configuration named as specified in `AZURE_SEMANTIC_CONFIGURATION_NAME` within the index settings in the Azure Portal *after* the index has been created by the processing script.

7.  **Prepare Data:**
    * Download the Kaggle Movie Dataset (`movies_metadata.csv`, `credits.csv`, etc.) if you haven't already. You can find datasets like "TMDB 5000 Movie Dataset" or similar ones containing the required columns.
    * Place `movies_metadata.csv` inside the `data/raw/kaggle_movie_dataset/` directory (create directories if they don't exist). Make sure the `SOURCE_FILE_PATH` in your `.env` file points correctly to this location *relative to the `notebooks` directory*.

## Data Processing

1.  **Navigate to Notebooks:**
    ```bash
    cd ../notebooks # Assuming you are still in the iac directory
    # Or cd notebooks from the project root
    ```
2.  **Run the Data Processing Notebook:**
    * Open and run the cells in `1_data_processing.ipynb` (using Jupyter Lab, VS Code, etc.).
    * This notebook will:
        * Read the `movies_metadata.csv` file.
        * Clean and prepare text data for embedding.
        * Call your local Ollama instance (`nomic-embed-text` model) to generate embeddings in batches.
        * Create or update the Azure AI Search index specified in your `.env` file.
        * Upload the movie data along with their embeddings to the index.
        * Save a backup of the processed data with embeddings to a `.jsonl` file in the `data/processed/` directory.
    * **Note:** This can take a significant amount of time depending on the number of records (`RECORDS_TO_PROCESS` in the notebook) and your machine's performance for Ollama. The script uploads data incrementally after each Ollama batch.

## Running the Application

1.  **Ensure Ollama is Running:** Make sure the `ollama serve nomic-embed-text` command is still active in its terminal.
2.  **Ensure `.env` is Correct:** Double-check that your `.env` file in the project root has the correct Azure Search endpoint, key, and index name.
3.  **Start Streamlit:** From the project root directory (where `requirements.txt` is):
    ```bash
    streamlit run src/app.py
    ```
4.  **Interact:** Open the URL provided by Streamlit (usually `http://localhost:8501`) in your web browser. Use the sidebar to select a search mode, enter your query, and click "Search Movies".

## Testing Search (Optional)

1.  **Navigate to Notebooks:**
    ```bash
    cd notebooks # If not already there
    ```
2.  **Run the Search Testing Notebook:**
    * Open and run the cells in `2_search_testing.ipynb`.
    * This notebook allows you to programmatically test different queries and search modes (`keyword`, `vector`, `hybrid`, `semantic_hybrid`) against your populated Azure AI Search index.
    * *Note:* This notebook currently uses the `/api/embeddings` Ollama endpoint, while the processing script and Streamlit app use `/api/embed`. Ensure your `OLLAMA_EMBEDDINGS_ENDPOINT` variable (or direct endpoint usage in the notebook) points to the correct place if you've standardized on one endpoint.

## Configuration Notes & Potential Issues

* **Ollama Model:** The project setup primarily uses `nomic-embed-text`. Ensure this model is pulled and served by Ollama. If you change the model, update `OLLAMA_MODEL` and `VECTOR_DIMENSION` in `.env` and potentially modify the embedding generation logic if the API response structure differs.
* **Ollama Endpoints:** Be aware of the potential discrepancy:
    * `1_data_processing.ipynb` uses `OLLAMA_ENDPOINT` (default `/api/embed`) with the correct batch payload.
    * `src/app.py` uses `OLLAMA_ENDPOINT` (default `/api/embed`) with the correct single-item payload.
    * `2_search_testing.ipynb` uses `OLLAMA_EMBEDDINGS_ENDPOINT` (default `/api/embeddings`) with the corresponding single-item payload (`prompt` key).
    If you encounter issues, ensure the endpoint used by each script/app matches the payload format it sends and the endpoint Ollama exposes. Standardizing on `/api/embed` might be preferable.
* **Azure Credentials:** Keep your `AZURE_SEARCH_API_KEY` secure. Do not commit the `.env` file to version control (it's included in `.gitignore`).
* **Semantic Search:** Requires a `basic` or higher tier Azure AI Search service, semantic search enabled for the tier, and a semantic configuration created *within the index* in the Azure portal matching the `AZURE_SEMANTIC_CONFIGURATION_NAME` in your `.env`.
* **Data Processing Time:** Generating embeddings for a large dataset can be time-consuming. Adjust `RECORDS_TO_PROCESS` in `1_data_processing.ipynb` for testing.
* **Memory Usage:** Processing large datasets and embedding batches can consume significant RAM. Adjust `OLLAMA_BATCH_SIZE` if you encounter memory issues.
