import streamlit as st
import os
import fitz  # PyMuPDF
import re
import pandas as pd
from tqdm import tqdm
import tempfile
from openai import OpenAI

def remove_special_characters(text):
    return re.sub(r"\s+", " ", text)

def analyze_page(page_content, client):
    prompt = f"""Given a page from a document containing various articles, analyze the content and identify sections that are related to crane projects. These projects could be about the purchasing of new cranes, expansion of ports that require new cranes, or modernization of cranes. The page may contain multiple articles or parts of articles.

Page content:
{page_content}

Provide a response in the following format:
Summary: [A brief summary of the page content]
Include or Exclude: [State whether this page should be included or excluded based on relevance to crane projects]
Reason: [Explain why this page should be included or excluded]
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes document content."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    # Parse the result into a dictionary
    lines = result.split('\n')
    parsed_result = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            parsed_result[key.strip()] = value.strip()

    return parsed_result

def process_pdfs(uploaded_files, api_key):
    results = []
    client = OpenAI(api_key=api_key)
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        doc = fitz.open(tmp_file_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            text = remove_special_characters(text)
            
            analysis = analyze_page(text, client)
            
            results.append({
                'filename': uploaded_file.name,
                'page': i + 1,
                'summary': analysis.get('Summary', 'N/A'),
                'include_or_exclude': analysis.get('Include or Exclude', 'N/A'),
                'reason': analysis.get('Reason', 'N/A')
            })
        
        doc.close()
        os.unlink(tmp_file_path)
    
    return results

def main():
    st.title("PDF Analysis App")
    
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")
    
    if uploaded_files and api_key:
        if st.button("Analyze PDFs"):
            with st.spinner("Analyzing PDFs..."):
                results = process_pdfs(uploaded_files, api_key)
            
            if results:
                df = pd.DataFrame(results)
                st.success("Analysis complete!")
                st.dataframe(df)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name="results.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No results were generated. Please check your PDF files and try again.")
    else:
        st.info("Please upload PDF files and provide an OpenAI API key to start the analysis.")

if __name__ == "__main__":
    main()