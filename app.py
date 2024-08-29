import streamlit as st
import os
import fitz  # PyMuPDF
from oai import analyze_page, init_openai
import re
import pandas as pd
from tqdm import tqdm
import tempfile

def remove_special_characters(text):
    return re.sub(r"\s+", " ", text)

def process_pdfs(uploaded_files, model, api_key, api_base):
    results = []
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        doc = fitz.open(tmp_file_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            text = remove_special_characters(text)
            
            analysis = analyze_page(text, model)
            
            try:
                results.append({
                    'filename': uploaded_file.name,
                    'page': i + 1,
                    'summary': analysis['summary'],
                    'include_or_exclude': analysis['include_or_exclude'],
                    'reason': analysis['reason']
                })
            except:
                st.error(f"Error analyzing page {i + 1} in file {uploaded_file.name}")
        
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
            model = init_openai(model=model_name, key=api_key, base=api_base)
            
            with st.spinner("Analyzing PDFs..."):
                results = process_pdfs(uploaded_files, model, api_key, api_base)
            
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
        st.info("Please upload PDF files and provide an API key to start the analysis.")

if __name__ == "__main__":
    main()