import streamlit as st
import asyncio
import pandas as pd
from pathlib import Path
import os
import networkx as nx
from pyvis.network import Network
import tempfile

# GraphRAG imports
from graphrag.config.load_config import load_config
import graphrag.api as api
from graphrag.utils.storage import load_table_from_storage
from graphrag.utils.api import create_storage_from_config

# Set page layout
st.set_page_config(page_title="86 - Eighty Six Knowledge Graph", layout="wide")

st.title("86 - Eighty Six: GraphRAG Query")

# Constants
ROOT_DIR = Path(".").resolve()
CONFIG_FILE = ROOT_DIR / "settings.yaml"


@st.cache_resource
def get_config():
    """Load GraphRAG configuration."""
    return load_config(root_dir=ROOT_DIR, config_filepath=CONFIG_FILE)


@st.cache_resource
def load_data(_config):
    """Load GraphRAG artifacts (Entities, Communities, Reports)."""
    dataframe_dict = {}
    storage_obj = create_storage_from_config(_config.output)

    # List of required tables for Global/Local search
    tables = [
        "entities",
        "communities",
        "community_reports",
        "text_units",
        "relationships"
    ]

    loaded_data = {}
    for name in tables:
        try:
            # We use asyncio.run because load_table_from_storage is async
            loaded_data[name] = asyncio.run(load_table_from_storage(name=name, storage=storage_obj))
        except Exception as e:
            st.warning(f"Could not load {name}: {e}")
            loaded_data[name] = pd.DataFrame()  # Return empty if missing

    return loaded_data


def build_networkx_graph(entities, relationships):
    """Build a NetworkX graph from entities and relationships."""
    G = nx.Graph()

    # Add nodes
    if not entities.empty and 'title' in entities.columns:
        for _, row in entities.iterrows():
            G.add_node(row['title'], type=row.get('type', 'Unknown'), description=row.get('description', ''))

    # Add edges
    if not relationships.empty and 'source' in relationships.columns and 'target' in relationships.columns:
        for _, row in relationships.iterrows():
            if row['source'] in G.nodes and row['target'] in G.nodes:
                # 'title' attribute in PyVis creates a hover tooltip
                desc = row.get('description', 'No description')
                G.add_edge(row['source'], row['target'], weight=row.get('weight', 1), title=desc)

    return G


def global_search(query, config, data):
    """Execute Global Search."""
    return asyncio.run(
        api.global_search(
            config=config,
            entities=data["entities"],
            communities=data["communities"],
            community_reports=data["community_reports"],
            community_level=2,  # Default level
            dynamic_community_selection=False,
            response_type="multiple paragraphs",
            query=query
        )
    )


def local_search(query, config, data):
    """Execute Local Search."""
    return asyncio.run(
        api.local_search(
            config=config,
            entities=data["entities"],
            communities=data["communities"],
            community_reports=data["community_reports"],
            text_units=data["text_units"],
            relationships=data["relationships"],
            covariates=None,
            community_level=2,
            response_type="multiple paragraphs",
            query=query
        )
    )


# Sidebar Configuration
st.sidebar.header("Configuration")

if not os.path.exists(ROOT_DIR / "output"):
    st.error("Output directory not found. Please run indexing first!")
    st.stop()

# Load resources
with st.spinner("Loading Index..."):
    try:
        config = get_config()
        data = load_data(config)
        st.sidebar.success("Index Loaded Successfully")
    except Exception as e:
        st.error(f"Failed to load index: {e}")
        st.stop()

# Tabs
tab1, tab2 = st.tabs(["Chat Query", "Graph Visualization"])

with tab1:
    search_type = st.radio("Search Type", ["Global Search", "Local Search"], horizontal=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about 86 - Eighty Six..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if search_type == "Global Search":
                        response, context = global_search(prompt, config, data)
                    else:
                        response, context = local_search(prompt, config, data)

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Optional: Show context/sources
                    with st.expander("View Context/Sources"):
                        st.write(context)

                except Exception as e:
                    st.error(f"Error during search: {e}")

with tab2:
    st.header("Knowledge Graph Visualization")

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        min_weight = st.slider("Minimum Edge Weight", min_value=1, max_value=50, value=10)
    with col2:
        max_nodes = st.slider("Max Nodes to Display", min_value=10, max_value=500, value=100)

    if st.button("Generate Graph"):
        with st.spinner("Building Graph Visualization..."):
            try:
                # Filter Relationships
                rels = data["relationships"]
                if not rels.empty and 'weight' in rels.columns:
                    rels_filtered = rels[rels['weight'] >= min_weight]
                else:
                    rels_filtered = rels

                # Build NetworkX Graph
                G = build_networkx_graph(data["entities"], rels_filtered)

                # Limit nodes if too huge
                if len(G.nodes) > max_nodes:
                    # Keep top nodes by degree
                    degrees = dict(G.degree)
                    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:max_nodes]
                    G = G.subgraph(top_nodes)

                # PyVis Visualization
                net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
                net.from_nx(G)

                # Physics options - Improve layout
                net.force_atlas_2based(gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0)

                # Save and display
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                    net.save_graph(tmp.name)
                    st.components.v1.html(Path(tmp.name).read_text(), height=750, width=1200, scrolling=True)

                st.success(f"Displaying {len(G.nodes)} nodes and {len(G.edges)} edges.")

            except Exception as e:
                st.error(f"Visualization Error: {e}")
