import streamlit as st
import os
import fitz  # PyMuPDF
import re
import pandas as pd
import tempfile
import requests

# Constants for Claude 3.5 Sonnet
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_KEY = "YOUR_CLAUDE_API_KEY"

def remove_special_characters(text):
    return re.sub(r"\s+", " ", text)

def analyze_page(page_content):
    prompt = f"""Given a page from a document containing various articles, analyze the content and identify sections that are related to crane projects. These projects could be about the purchasing of new cranes, expansion of ports that require new cranes, or modernization of cranes. The page may contain multiple articles or parts of articles.

Page content:
{page_content}

Provide a response in the following format:
Summary: [A brief summary of the page content]
Include or Exclude: [State whether this page should be included or excluded based on relevance to crane projects]
Reason: [Explain why this page should be included or excluded]
"""
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000
    }

    response = requests.post(CLAUDE_API_URL, headers=headers, json=data)

    if response.status_code != 200:
        st.error(f"Error: {response.status_code} - {response.text}")
        raise Exception(f"API Request failed: {response.text}")

    result = response.json()['content'][0]['text']

    lines = result.split('\n')
    parsed_result = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            parsed_result[key.strip()] = value.strip()

    return parsed_result

def extract_projects(text):
    prompt = f"""Analyze the following text and extract specific crane projects mentioned. For each project, provide:
1. The number and type of cranes (e.g., RTG, STS)
2. The location (port name and country if available)

Format the output as a list of strings, each in the format: "[Number] [Type] cranes in [Location]"

If multiple projects are mentioned, list each one separately. If the exact number is not specified, use "Multiple" for the number.

Text to analyze:
{text}
"""

    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": CLAUDE_API_KEY
    }

    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000
    }

    response = requests.post(CLAUDE_API_URL, headers=headers, json=data)

    if response.status_code != 200:
        st.error(f"Error: {response.status_code} - {response.text}")
        raise Exception(f"API Request failed: {response.text}")

    result = response.json()['content'][0]['text']

    return [line.strip() for line in result.split('\n') if line.strip()]

def process_pdfs(uploaded_files):
    results = []
    projects = []

    total_pages = 0
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Only proceed if the file is not empty and is a valid PDF
        if os.path.getsize(tmp_file_path) == 0:
            st.warning(f"The file {uploaded_file.name} is empty and will be skipped.")
            os.unlink(tmp_file_path)
            continue
        
        try:
            doc = fitz.open(tmp_file_path)
            total_pages += len(doc)
            doc.close()
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")
            os.unlink(tmp_file_path)
            continue
        
        os.unlink(tmp_file_path)

    progress_bar = st.progress(0)
    current_page = 0
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        doc = fitz.open(tmp_file_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            text = remove_special_characters(text)
            
            analysis = analyze_page(text)
            
            result = {
                'filename': uploaded_file.name,
                'page': i + 1,
                'summary': analysis.get('Summary', 'N/A'),
                'include_or_exclude': analysis.get('Include or Exclude', 'N/A'),
                'reason': analysis.get('Reason', 'N/A')
            }
            
            if analysis.get('Include or Exclude', '').lower() == 'include':
                page_projects = extract_projects(text)
                projects.extend([(uploaded_file.name, i + 1, project) for project in page_projects])
            
            results.append(result)
            
            current_page += 1
            progress_bar.progress(current_page / total_pages)
        
        doc.close()
        os.unlink(tmp_file_path)
    
    return results, projects

def main():
    st.title("PDF Analysis App")
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'projects' not in st.session_state:
        st.session_state.projects = None
    
    claude_api_key = st.sidebar.text_input("Claude API Key", type="password")
    
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")
    
    if uploaded_files and claude_api_key:
        global CLAUDE_API_KEY
        CLAUDE_API_KEY = claude_api_key

        if st.button("Analyze PDFs"):
            with st.spinner("Analyzing PDFs..."):
                st.session_state.results, st.session_state.projects = process_pdfs(uploaded_files)
            
            st.success("Analysis complete!")
    
    if st.session_state.results:
        st.subheader("Analysis Results")
        df = pd.DataFrame(st.session_state.results)
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name="pdf_analysis_results.csv",
            mime="text/csv",
        )
    
    if st.session_state.projects:
        st.subheader("Extracted Projects")
        projects_df = pd.DataFrame(st.session_state.projects, columns=['Filename', 'Page', 'Project'])
        st.dataframe(projects_df)
        
        projects_csv = projects_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download projects as CSV",
            data=projects_csv,
            file_name="extracted_projects.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()