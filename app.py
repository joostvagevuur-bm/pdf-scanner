import streamlit as st
import os
import fitz  # PyMuPDF
import re
import pandas as pd
from tqdm import tqdm
import tempfile
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

# Define the schemas for the output
response_schemas = [
    ResponseSchema(name="summary", description="Summary of the Page"),
    ResponseSchema(name="include_or_exclude", description="Include or Exclude"),
    ResponseSchema(name="reason", description="Reason")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# Define the prompt template
prompt_template = """Given a page from a document containing various articles, analyze the content and identify sections that are related to crane projects. These projects could be about the purchasing of new cranes, expansion of ports that require new cranes, or modernization of cranes. The page may contain multiple articles or parts of articles.

Page content:
{doc}

{format_instructions}
"""

def remove_special_characters(text):
    return re.sub(r"\s+", " ", text)

def init_openai(model, key, base):
    return ChatOpenAI(model=model, openai_api_key=key, openai_api_base=base)

def analyze_page(page_content, oai_model):
    chat_prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = chat_prompt | oai_model | output_parser
    result = chain.invoke({"doc": page_content, "format_instructions": output_parser.get_format_instructions()})
    return result

def process_pdfs(uploaded_files, model, api_key, api_base):
    results = []
    oai_model = init_openai(model=model, key=api_key, base=api_base)
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        doc = fitz.open(tmp_file_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            text = remove_special_characters(text)
            
            analysis = analyze_page(text, oai_model)
            
            results.append({
                'filename': uploaded_file.name,
                'page': i + 1,
                'summary': analysis['summary'],
                'include_or_exclude': analysis['include_or_exclude'],
                'reason': analysis['reason']
            })
        
        doc.close()
        os.unlink(tmp_file_path)
    
    return results

def main():
    st.title("PDF Analysis App")
    
    st.sidebar.header("Configuration")
    model_name = st.sidebar.selectbox("Select Model", ["gpt-3.5-turbo", "gpt-4-turbo"])
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    api_base = st.sidebar.text_input("API Base URL", value="https://api.openai.com/v1")
    
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")
    
    if uploaded_files and api_key:
        if st.button("Analyze PDFs"):
            with st.spinner("Analyzing PDFs..."):
                results = process_pdfs(uploaded_files, model_name, api_key, api_base)
            
            if results:
                df = pd.DataFrame(results)
                st.success("Analysis complete!")
                st.dataframe(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name=f"results_{model_name}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No results were generated. Please check your PDF files and try again.")
    else:
        st.info("Please upload PDF files and provide an OpenAI API key to start the analysis.")

if __name__ == "__main__":
    main()