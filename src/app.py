import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
)

# --- Configuration Loading ---
try:
    load_dotenv()
except Exception as e:
    # Keep this print for critical load error, but log it properly in production
    print(f"Error loading .env file: {e}")
    st.error(f"Critical Error loading .env file: {e}")
    st.stop()


# Azure AI Search Config (ensure these are set in your .env or environment)
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX_NAME")

# Ollama Config
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/embed")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
VECTOR_DIMENSION = os.getenv("VECTOR_DIMENSION") # Load as string first

# --- Helper Functions --- (Keep functions as they are)
# @st.cache_data(show_spinner=False) # Keep disabled if testing, re-enable later if needed
def get_ollama_embedding(text: str, model: str, endpoint: str, expected_dimension: int):
    """Calls the local Ollama API (/api/embed) to get a single embedding.""" # Docstring updated
    if not text or not text.strip():
        return None

    # --- Print params *inside function* before request (Optional Debugging) ---
    print(f"\n--- Inside get_ollama_embedding (Using /api/embed logic) ---")
    print(f"Received text: '{text}'")
    print(f"Using model: '{model}'")
    print(f"Targeting endpoint: '{endpoint}'") # Should now be the /api/embed endpoint
    # ---

    try:
        # --- MODIFIED PAYLOAD for /api/embed ---
        # Send the single text within a list for the "input" key
        payload = {"model": model, "input": [text]}
        print(f"DEBUG: Sending Payload to /api/embed: {json.dumps(payload)}")
        # ---

        response = requests.post(
            endpoint, # Ensure this points to /api/embed
            json=payload,
            timeout=60
        )

        # --- Log response details (Optional Debugging) ---
        print(f"DEBUG: Response Status Code: {response.status_code}")
        print(f"DEBUG: Response Headers: {response.headers}")
        print(f"DEBUG: Response Raw Text: {response.text}")
        # ---

        response.raise_for_status()
        response_json = response.json()
        print(f"DEBUG: Parsed Response JSON from /api/embed: {response_json}")

        embedding = None
        # --- PARSING LOGIC for /api/embed response ---
        # Expects {"embeddings": [ [vector] ]} for a single input
        if "embeddings" in response_json and isinstance(response_json["embeddings"], list):
            embeddings_list = response_json["embeddings"]
            if len(embeddings_list) == 1 and isinstance(embeddings_list[0], list):
                 # Successfully got the embedding list for our single input
                 embedding = embeddings_list[0]
                 print(f"DEBUG: Extracted embedding vector (Dim: {len(embedding)})") # Log success
            elif len(embeddings_list) == 0:
                 st.error(f"Ollama (/api/embed) returned an empty list within 'embeddings'. Response: {response_json}")
                 print(f"ERROR: Ollama (/api/embed) returned empty list within 'embeddings'. Response: {response_json}")
                 return None
            else:
                # Should not happen for single input, but handle defensively
                st.error(f"Ollama (/api/embed) returned unexpected number of embeddings ({len(embeddings_list)}) for single input. Response: {response_json}")
                print(f"ERROR: Ollama (/api/embed) returned unexpected embedding count. Response: {response_json}")
                return None
        else:
             st.error(f"Error: 'embeddings' key missing or invalid in Ollama response from /api/embed. Response: {response_json}")
             print(f"ERROR: 'embeddings' key missing/invalid from /api/embed. Response: {response_json}")
             return None
        # --- END PARSING LOGIC ---


        # Validate the found embedding dimension (Keep this check)
        if embedding:
            if expected_dimension and len(embedding) != expected_dimension:
                st.error(f"Ollama returned embedding with dimension {len(embedding)}, expected {expected_dimension}. Check OLLAMA_MODEL/VECTOR_DIMENSION.")
                print(f"ERROR: Dimension mismatch. Got {len(embedding)}, expected {expected_dimension}.")
                return None
            return embedding # Return the valid embedding

    # --- Keep your existing exception handling ---
    except requests.exceptions.Timeout as e:
         st.error(f"Error: Ollama API request timed out ({endpoint}). Is Ollama running?")
         print(f"ERROR: Ollama Timeout - {e}")
    except requests.exceptions.ConnectionError as e:
         st.error(f"Error: Could not connect to Ollama API at {endpoint}. Is Ollama running?")
         print(f"ERROR: Ollama ConnectionError - {e}")
    except requests.exceptions.RequestException as e:
         st.error(f"Error calling Ollama API: {e}")
         print(f"ERROR: Ollama RequestException - {e}")
    except json.JSONDecodeError as e:
         raw_text = "Could not get raw text"
         if 'response' in locals() and hasattr(response, 'text'):
              raw_text = response.text
         st.error(f"Error: Could not decode JSON response from Ollama API. Response Text: {raw_text}")
         print(f"ERROR: Ollama JSONDecodeError - {e} - Raw Text: {raw_text}")
    return None # Ensure return None on exceptions
    """Calls the local Ollama API to get a single embedding.
       Handles both 'embedding' and 'embeddings' keys in response.
    """
    if not text or not text.strip():
        return None
    try:
        
        response = requests.post(
            endpoint,
            json={"model": model, "prompt": text},
            timeout=60
        )
        response.raise_for_status()
        response_json = response.json()

        embedding = None
        # Check for plural 'embeddings' first (seems to be what was returned)
        if "embeddings" in response_json and isinstance(response_json["embeddings"], list):
            if len(response_json["embeddings"]) == 1 and isinstance(response_json["embeddings"][0], list):
                 embedding = response_json["embeddings"][0] # Take the first embedding if list not empty
            elif len(response_json["embeddings"]) == 0:
                 st.error(f"Ollama returned an empty list for 'embeddings'. Response: {response_json}")
                 return None # Explicitly handle empty list case

        # Fallback check for singular 'embedding'
        elif "embedding" in response_json and isinstance(response_json["embedding"], list):
            if len(response_json["embedding"]) > 0:
                 embedding = response_json["embedding"]
            else:
                 st.error(f"Ollama returned an empty list for 'embedding'. Response: {response_json}")
                 return None # Explicitly handle empty list case

        # Validate the found embedding
        if embedding:
            # Validate dimension
            if expected_dimension and len(embedding) != expected_dimension:
                st.error(f"Ollama returned embedding with dimension {len(embedding)}, expected {expected_dimension}. Check your OLLAMA_MODEL and VECTOR_DIMENSION settings.")
                return None
            return embedding # Return the valid embedding
        else:
            # If neither key was found or list was empty (and not handled above)
            st.error(f"Error: Valid embedding key ('embedding' or 'embeddings') missing or invalid in Ollama response. Response: {response_json}")
            return None

    except requests.exceptions.Timeout:
        st.error(f"Error: Ollama API request timed out ({endpoint}). Is Ollama running and responding?")
    except requests.exceptions.ConnectionError:
        st.error(f"Error: Could not connect to Ollama API at {endpoint}. Is Ollama running?")
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling Ollama API: {e}")
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON response from Ollama API. Response Text: {response.text}")
    return None # Ensure return None on exceptions
def display_results(results):
    """Displays search results nicely in Streamlit."""
    try:
        count = results.get_count()
        st.subheader(f"Found {count} results:") # Use get_count() for total matching docs
    except Exception as e:
        st.error(f"Error getting result count: {e}")
        st.subheader("Results:") # Fallback
        return # Stop if we can't even get the count

    if count == 0:
         st.write("No results found.")
         return

    for i, result in enumerate(results):
        score = result.get('@search.score', 'N/A') # Standard relevance score
        reranker_score = result.get('@search.reranker_score', 'N/A') # Semantic reranker score
        caption_text = "N/A"
        caption_highlights = "N/A"

        # Extract semantic captions if available
        if "@search.captions" in result and result["@search.captions"]:
            caption = result["@search.captions"][0]
            caption_text = caption.text
            caption_highlights = caption.highlights if caption.highlights else caption_text # Fallback

        with st.expander(f"**{i+1}. {result.get('title', 'No Title')}** (Score: {score:.4f}, Reranker Score: {reranker_score})"):
            st.markdown(f"**Movie ID:** `{result.get('movie_id', 'N/A')}`")
            st.markdown(f"**Overview:** {result.get('overview', 'N/A')}")
            st.markdown(f"**Tagline:** *{result.get('tagline', 'N/A')}*")
            st.markdown(f"**Genres:** {result.get('genres', 'N/A')}")

            # Display semantic caption if present
            if caption_text != "N/A":
                st.markdown("---")
                st.markdown(f"**Semantic Caption:**")
                st.markdown(caption_highlights, unsafe_allow_html=True) # Use highlights if available

# --- Basic Ollama Check ---
@st.cache_data(ttl=60) # Cache the check result for 60 seconds
def check_ollama(endpoint):
    """Checks if the base Ollama endpoint is reachable."""
    try:
        # Use a simpler endpoint like '/' or '/api/tags' for a basic check
        check_url = endpoint
        if "/api/embeddings" in endpoint: # Try to get the base URL
            check_url = endpoint.split("/api/embeddings")[0] + "/"
        elif "/api/embed" in endpoint: # Handle older possibility
             check_url = endpoint.split("/api/embed")[0] + "/"

        response = requests.get(check_url, timeout=5) # Check base endpoint
        response.raise_for_status()
        return True # Ollama is reachable
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException):
        # Don't show error directly here, let the caller handle UI feedback
        return False # Ollama is not reachable


# --- Streamlit App UI ---
st.set_page_config(page_title="Contoso Movie Company", layout="wide")
st.image("contoso.png")
st.title("🎬 Movie Search Demo (Azure AI Search + Ollama)")


# --- Validate Configuration Early ---
config_errors = []
if not AZURE_SEARCH_ENDPOINT: config_errors.append("AZURE_SEARCH_SERVICE_ENDPOINT is not set.")
if not AZURE_SEARCH_KEY: config_errors.append("AZURE_SEARCH_API_KEY is not set.")
if not AZURE_SEARCH_INDEX: config_errors.append("AZURE_SEARCH_INDEX_NAME is not set.")
if not OLLAMA_ENDPOINT: config_errors.append("OLLAMA_ENDPOINT is not set.")
if not OLLAMA_MODEL: config_errors.append("OLLAMA_MODEL is not set.")
if not VECTOR_DIMENSION:
    config_errors.append("VECTOR_DIMENSION is not set.")
else:
    try:
        VECTOR_DIMENSION = int(VECTOR_DIMENSION) # Convert to int now
    except ValueError:
        config_errors.append(f"VECTOR_DIMENSION ('{VECTOR_DIMENSION}') is not a valid integer.")

# Display config errors prominently if any
if config_errors:
    st.error("Configuration Errors Found:\n- " + "\n- ".join(config_errors))
    st.stop() # Stop execution if essential config is missing/invalid
else:
    st.caption(f"Using Azure AI Search Index: `{AZURE_SEARCH_INDEX}` | Ollama Model: `{OLLAMA_MODEL}`")

# --- Sidebar for Configuration and Controls ---
with st.sidebar:
    st.header("Configuration Status")
    # Simplified Status: Show general config load status
    st.success("Azure & Ollama Config Loaded")

    # Perform Ollama check and show status
    ollama_ok = check_ollama(OLLAMA_ENDPOINT)
    if ollama_ok:
         st.success("Ollama service reachable.")
    else:
         st.error("Ollama service NOT reachable. Check terminal & ensure Ollama is running.")
         # Optional: You could stop the app if Ollama is essential for all operations
         # st.stop()

    # Keep Search Settings section as is
    st.header("Search Settings")
    search_mode = st.selectbox(
        "Select Search Mode:",
        ("Keyword", "Vector", "Hybrid", "Semantic (Keyword + Semantic Reranking)"),
        key="search_mode_select" # Add a key for stability
    )
    top_k = st.slider("Number of results (k):", min_value=1, max_value=20, value=5, key="top_k_slider")

    st.markdown("---")
    st.markdown(
        """
        **Search Modes Explained:**
        - **Keyword:** Standard text search (BM25).
        - **Vector:** Semantic similarity search using embeddings. Finds conceptually related items.
        - **Hybrid:** Combines Keyword and Vector results (RRF). Good for balancing relevance and recall.
        - **Semantic:** Uses Keyword search first, then applies a Microsoft deep learning model to re-rank results and optionally extract captions/answers. *Requires Semantic Search enabled on your Azure Search index.*
        """
    )

# --- Main Search Area --- (Code remains the same from here)
query = st.text_input("Enter your movie search query:", placeholder="e.g., futuristic space battles", key="query_input")

search_button = st.button("Search Movies", key="search_button")

# --- Perform Search on Button Click ---
if search_button and query:
    st.write(f"Performing **{search_mode}** search for: *'{query}'*")
    start_time = time.time()

    # --- Initialize Azure Search Client ---
    search_client = None # Initialize as None
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY)
        )
    except Exception as e:
        st.error(f"Error creating Azure Search client: {e}")
        st.stop() # Stop if client can't be created

    results = None
    vector_query = None

    # --- Generate Query Embedding (if needed) ---
    if "Vector" in search_mode or "Hybrid" in search_mode:
        if not ollama_ok: # Check if Ollama was reachable earlier
             st.error("Cannot perform Vector/Hybrid search because Ollama service is not reachable.")
        else:
            with st.spinner(f"Generating query embedding using {OLLAMA_MODEL}..."):
                vector_query = get_ollama_embedding(query, OLLAMA_MODEL, OLLAMA_ENDPOINT, VECTOR_DIMENSION)
            if not vector_query:
                # Error is already shown by get_ollama_embedding if it failed
                st.warning("Failed to generate query embedding. Cannot perform Vector or Hybrid search.")
            else:
                st.success("Query embedding generated.")

    # --- Execute Search Based on Mode ---
    if search_client: # Proceed only if client was created
        with st.spinner("Searching..."):
            try:
                if search_mode == "Keyword":
                    results = search_client.search(
                        search_text=query,
                        select="movie_id,title,overview,tagline,genres", # Select fields to return
                        top=top_k,
                        include_total_count=True
                    )

                elif search_mode == "Vector":
                    if vector_query: # Check if embedding succeeded
                        vector_query_object = VectorizedQuery(vector=vector_query, k_nearest_neighbors=top_k, fields="embedding")
                        results = search_client.search(
                            search_text=None, # No keyword search
                            vector_queries=[vector_query_object],
                            select="movie_id,title,overview,tagline,genres",
                            top=top_k,
                            include_total_count=True
                        )
                    else:
                        # Warning about skipping vector search if embedding failed
                        if ollama_ok: # Only show if Ollama was ok but embedding failed
                            st.warning("Skipping Vector search as query embedding failed.")


                elif search_mode == "Hybrid":
                    if vector_query: # Check if embedding succeeded
                        vector_query_object = VectorizedQuery(vector=vector_query, k_nearest_neighbors=top_k, fields="embedding")
                        results = search_client.search(
                            search_text=query, # Keyword part
                            vector_queries=[vector_query_object], # Vector part
                            select="movie_id,title,overview,tagline,genres",
                            top=top_k,
                            include_total_count=True
                            # Azure Search handles the RRF ranking automatically
                        )
                    else:
                         # Warning about skipping hybrid search if embedding failed
                        if ollama_ok: # Only show if Ollama was ok but embedding failed
                            st.warning("Skipping Hybrid search as query embedding failed.")
                elif search_mode == "Semantic (Keyword + Semantic Reranking)":
                    try:
                        results = search_client.search(
                            search_text=query,
                            select="movie_id,title,overview,tagline,genres",
                            query_type=QueryType.SEMANTIC, 
                            semantic_configuration_name=os.environ.get("AZURE_SEMANTIC_CONFIGURATION_NAME"), # ASSUMPTION: You have a 'default' semantic config. Change if needed.
                            query_caption=QueryCaptionType.EXTRACTIVE, # Try to extract captions
                            query_answer=QueryAnswerType.EXTRACTIVE, # Try to extract answers (may not apply well to movies)
                            top=top_k,
                            include_total_count=True
                        )
                        st.info("Note: Semantic search requires a Semantic Configuration to be enabled and set up on your Azure AI Search Index.")
                    except Exception as semantic_error:
                        st.error(f"Semantic Search Error: {semantic_error}. Is Semantic Search enabled and configured on the index '{AZURE_SEARCH_INDEX}' with a 'default' configuration?")
                        results = None # Prevent displaying results from failed attempt


            except Exception as e:
                st.error(f"An error occurred during search: {e}")

        end_time = time.time()
        search_duration = end_time - start_time
        st.write(f"Search completed in {search_duration:.2f} seconds.")


        # --- Display Results ---
        if results:
            display_results(results)
        # Handle cases where search was skipped or failed silently
        elif ("Vector" in search_mode or "Hybrid" in search_mode) and not vector_query:
             # Error/Warning about embedding failure was already shown
             pass # Avoid redundant messages
        elif not results and "Semantic" in search_mode:
             # Error about semantic failure was already shown
             pass
        elif not results:
             st.info("No results found for your query.")


elif search_button and not query:
    st.warning("Please enter a search query.")