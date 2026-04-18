import streamlit as st
import requests
import os

# The Docker network URL for the FastAPI backend
API_URL = "http://api:8000"
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "REDACTED")
HEADERS = {"X-API-Key": BACKEND_API_KEY}

st.set_page_config(page_title="CodeRAG", layout="wide")
st.title("💻 Codebase RAG Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            with st.expander("Sources"):
                for cite in message["citations"]:
                    st.code(cite, language="text")

# Accept user input
if prompt := st.chat_input("Ask a question about the codebase..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking & searching codebase..."):
            try:
                # -> THIS IS THE CRITICAL UPDATE <-
                # We inject the headers so FastAPI knows we have permission
                response = requests.post(
                    f"{API_URL}/query", 
                    json={"question": prompt},
                    headers=HEADERS
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("answer", "No answer generated.")
                citations = data.get("citations", [])
                
                st.markdown(answer)
                if citations:
                    with st.expander("Sources"):
                        for cite in citations:
                            # Pro-tip: Changed language="text" to language="python" for better syntax highlighting!
                            st.code(cite, language="python")
                            
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "citations": citations
                })
                
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the backend: {e}")