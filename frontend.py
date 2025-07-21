import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete
from snowflake.core import Root
import pandas as pd
import json

# Set pandas display options
pd.set_option("max_colwidth", None)

# Default Values
NUM_CHUNKS = 3  # Num-chunks provided as context
SLIDE_WINDOW = 7  # Number of previous messages to remember

# Service parameters
CORTEX_SEARCH_DATABASE = "CC_QUICKSTART_CORTEX_SEARCH_DOCS"
CORTEX_SEARCH_SCHEMA = "DATA"
CORTEX_SEARCH_SERVICE = "CC_SEARCH_SERVICE_CS"

# Columns to query in the service
COLUMNS = ["chunk", "relative_path", "category"]

# Snowflake session
session = get_active_session()
root = Root(session)
svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]


### Functions ###

def config_options():
    st.sidebar.title("⚙️ Configuration")

    # Model selection
    st.sidebar.selectbox(
        "Select your model:",
        ('mistral-large2','mixtral-8x7b', 'snowflake-arctic', 
         'llama3-8b', 'llama3-70b', 'reka-flash',
         'mistral-7b', 'llama2-70b-chat', 'gemma-7b'),
        key="model_name"
    )

    # Categories selection
    categories = session.table('docs_chunks_table').select('category').distinct().collect()
    cat_list = ['ALL'] + [cat.CATEGORY for cat in categories]
    st.sidebar.selectbox("Select a category:", cat_list, key="category_value")

    # Options for using history and debugging
    st.sidebar.checkbox("Remember chat history", key="use_chat_history", value=True)
    st.sidebar.checkbox("Debug mode", key="debug", value=True)

    # Option to use document context
    st.sidebar.checkbox("Use your own document for context", key="use_document_context", value=True)

    # Clear conversation button
    if st.sidebar.button("Start New Chat"):
        st.session_state.messages = []  # Clear chat history


def init_messages():
    """Initialize chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def get_similar_chunks_search_service(query):
    """Fetch similar document chunks using the search service."""
    if st.session_state.category_value == "ALL":
        response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
    else:
        filter_obj = {"@eq": {"category": st.session_state.category_value}}
        response = svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)

    # Parse the response to a Python dictionary
    response_dict = json.loads(response.json()) if isinstance(response.json(), str) else response.json()

    if st.session_state.debug:
        st.sidebar.json(response_dict)

    return response_dict


def get_chat_history():
    """Retrieve the last N messages for context."""
    start_index = max(0, len(st.session_state.messages) - SLIDE_WINDOW)
    return st.session_state.messages[start_index:]


def create_prompt(myquestion):
    """Generate a prompt for the LLM."""
    chat_history = get_chat_history() if st.session_state.use_chat_history else []

    if st.session_state.use_document_context:
        if chat_history:
            question_summary = summarize_question_with_history(chat_history, myquestion)
            prompt_context = get_similar_chunks_search_service(question_summary)
        else:
            prompt_context = get_similar_chunks_search_service(myquestion)
    else:
        prompt_context = {"results": []}  # No context if the user disables it

    prompt = f"""
        You are an expert assistant that extracts information from the CONTEXT provided.
        Use the CHAT HISTORY and CONTEXT to answer the QUESTION concisely and accurately.
        Do not hallucinate; only use the information provided.
        
        <chat_history>
        {chat_history}
        </chat_history>
        <context>
        {prompt_context}
        </context>
        <question>
        {myquestion}
        </question>
        Answer:
    """
    
    relative_paths = set(
        item['relative_path'] for item in prompt_context.get('results', [])
    )
    return prompt, relative_paths


def summarize_question_with_history(chat_history, question):
    """Summarize chat history and extend the question."""
    prompt = f"""
        Based on the chat history and the question, extend the question contextually.
        <chat_history>
        {chat_history}
        </chat_history>
        <question>
        {question}
        </question>
        Provide only the summarized query:
    """
    summary = Complete(st.session_state.model_name, prompt)
    if st.session_state.debug:
        st.sidebar.text("Generated Query for Context:")
        st.sidebar.caption(summary)
    return summary.strip()


def answer_question(myquestion):
    """Answer the user's question."""
    prompt, relative_paths = create_prompt(myquestion)
    response = Complete(st.session_state.model_name, prompt)
    return response.strip(), relative_paths


def main():
    st.title("🤖 UniTech Knowledge Assistant")
    st.write("🎓 Empowering University Students with Smart Document Insights and AI-Powered Assistance")

    config_options()
    init_messages()

    # Display available documents
    st.subheader("Available Documents")
    docs_available = session.sql("ls @docs").collect()
    if docs_available:
        st.dataframe([doc["name"] for doc in docs_available], use_container_width=True)
    else:
        st.write("No documents found.")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input for questions
    if user_question := st.chat_input("Ask a question about your documents:"):
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("Processing your query..."):
                response, relative_paths = answer_question(user_question)
                placeholder.markdown(response)

                # Display related document links
                if relative_paths:
                    with st.sidebar.expander("Related Documents"):
                        for path in relative_paths:
                            cmd2 = f"SELECT GET_PRESIGNED_URL(@docs, '{path}', 360) AS URL_LINK FROM directory(@docs)"
                            df_url_link = session.sql(cmd2).to_pandas()
                            url_link = df_url_link.loc[0, 'URL_LINK']
                            display_url = f"Doc: [{path}]({url_link})"
                            st.sidebar.markdown(display_url)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
