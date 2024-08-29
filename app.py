import streamlit as st
import os
import fitz  # PyMuPDF
from openai import OpenAI
import re
import pandas as pd
import tempfile

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
        model="gpt-4o-latest",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes document content."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    lines = result.split('\n')
    parsed_result = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            parsed_result[key.strip()] = value.strip()

    return parsed_result

def extract_projects(text, client):
    prompt = f"""Analyze the following text and extract specific crane projects mentioned. For each project, provide:
1. The number and type of cranes (e.g., RTG, STS)
2. The location (port name and country if available)

Format the output as a list of strings, each in the format: "[Number] [Type] cranes in [Location]"

If multiple projects are mentioned, list each one separately. If the exact number is not specified, use "Multiple" for the number.

Text to analyze:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-latest",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts project information."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    return [line.strip() for line in result.split('\n') if line.strip()]

def process_pdfs(uploaded_files, api_key):
    results = []
    projects = []
    client = OpenAI(api_key=api_key)
    
    total_pages = sum(len(fitz.open(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)) for uploaded_file in uploaded_files)
    progress_bar = st.progress(0)
    current_page = 0
    
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        # Check if the file is empty before proceeding
        if os.path.getsize(tmp_file_path) == 0:
            st.warning(f"The file {uploaded_file.name} is empty and will be skipped.")
            os.unlink(tmp_file_path)
            continue

        doc = fitz.open(tmp_file_path)
        
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            text = remove_special_characters(text)
            
            analysis = analyze_page(text, client)
            
            result = {
                'filename': uploaded_file.name,
                'page': i + 1,
                'summary': analysis.get('Summary', 'N/A'),
                'include_or_exclude': analysis.get('Include or Exclude', 'N/A'),
                'reason': analysis.get('Reason', 'N/A')
            }
            
            if analysis.get('Include or Exclude', '').lower() == 'include':
                page_projects = extract_projects(text, client)
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
    
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")
    
    if uploaded_files and api_key:
        if st.button("Analyze PDFs"):
            st.session_state.results = []
            st.session_state.projects = []
            for file in uploaded_files:
                st.write(f"Analyzing {file.name}...")
                results, projects = process_pdfs([file], api_key)
                st.session_state.results.extend(results)
                st.session_state.projects.extend(projects)
            st.success("Analysis complete!")
    
    if st.session_state.results:
        df = pd.DataFrame(st.session_state.results)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name="results.csv",
            mime="text/csv",
        )
        
        if st.session_state.projects:
            if st.button("Show Projects"):
                project_df = pd.DataFrame(st.session_state.projects, columns=['Filename', 'Page', 'Project'])
                st.write("### Extracted Projects")
                st.table(project_df)
        else:
            st.info("No projects were found in the analyzed pages.")
    elif uploaded_files:
        st.info("Click 'Analyze PDFs' to start the analysis.")
    else:
        st.info("Please upload PDF files and provide an OpenAI API key to start the analysis.")

if __name__ == "__main__":
    main()
