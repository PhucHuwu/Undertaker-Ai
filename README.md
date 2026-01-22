# 86 - Eighty Six GraphRAG

![Knowledge Graph Visualization](graph_preview.png)

This project implements a Retrieval-Augmented Generation (RAG) system using **GraphRAG** for the novel "86 - Eighty Six".

## Architecture

- **Engine**: Microsoft GraphRAG
- **LLM**: Mistral Devstral (via OpenRouter)
- **UI**: Streamlit

## Setup

1. **Environment**:

    ```bash
    conda activate RAG-test
    pip install -r requirements.txt # (If created) or ensure graphrag is installed
    ```

2. **Configuration**:
    - `settings.yaml` is configured for OpenRouter.
    - `.env` contains `GRAPHRAG_API_KEY`.

## Usage

### 1. Indexing (Build Knowledge Graph)

To rebuild the index (if dataset changes):

```bash
conda run -n RAG-test graphrag index --root .
```

### 2. Querying (Streamlit UI)

To launch the chat interface:

```bash
conda run -n RAG-test streamlit run app.py
```

## Project Structure

- `input/`: Contains the novel dataset (`dataset.txt`).
- `output/`: Contains the generated Knowledge Graph artifacts (Parquet files).
- `libs/`: External libraries (Semantica).
- `app.py`: Streamlit application.
- `settings.yaml`: GraphRAG configuration.
