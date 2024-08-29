
# Project Completion Overview

This document provides a detailed overview of the completed project, ensuring you have all the information needed to install and operate the developed application efficiently.

## Installation Steps

Before you start using the application, it's crucial to set up your environment correctly by installing all necessary dependencies. Python should already be installed on your computer. I have exported the environment settings, run the following command to install them:

   ```bash
   pip install -r requirements.txt
   ```

## How to Use

Place all the PDF files you need to analyze into the `pdf_files` folder (for example, the samples you've sent me). 📂 You can run the application via the command line. Below, you'll find detailed explanations of the command-line parameters along with examples showing how to effectively use the application with various API keys and base URLs.

### Command-Line Parameters

- `--model`: Specifies which OpenAI model to use. The default setting is `gpt-3.5-turbo`.
- `--api_base`: Designates the OpenAI API base URL. The default is `https://api.openai.com/v1`.
- `--api_key`: Required for authentication. Please provide your OpenAI API key.

### Script Functionality

- The script is designed to read PDF files from a folder named `pdf_files`.
- Each PDF file is processed to extract text and analyze its content with the specified OpenAI model.
- The script removes special characters from the text to enhance the accuracy of the analysis.
- The results, which include summaries of pages and their relevance based on specific criteria, are compiled into a DataFrame.
- The DataFrame is then exported to an Excel file named `results_{model_name}.xlsx`.

### Example Usage Commands

1. **Using the standard API base and your provided API key**:

   ```bash
   python .\main.py --api_key your_api_key_here
   ```

2. **Using my provided test account**:

   ```bash
   python .\main.py --api_base https://api.enfp.im/v1 --model gpt-4-turbo --api_key sk-piIlwYwHiVn9IlKsEe8b209aC32b494191Cc58F313198d4b
   ```
   You will need to specify the API key here, but you can use this parameter for yourself. You can run the command above to complete the PDF analysis. This test account has a $30 balance, which you can use for testing or any other purposes. 🚀

## Additional Notes

- I have analyzed all the PDF files you sent me, providing results for both gpt-3.5 and gpt-4, with details on every page. I believe they meet your needs. Please review them, and of course, let me know if there are any adjustments needed.

- gpt-3.5 or gpt-4? That's a good question. I think gpt-3.5 is much faster and more cost-effective while the quality of responses is not bad. I recommend it. Of course, you can use the command line parameter `--model gpt-4-turbo` to customize the model you need.
- The other two files, `oai.py` and `function_calling.py`, are necessary to ensure structured responses and to interface with OpenAI's services.
- In the era of large models, code is always simple. We need to spend more time on prompt engineering and structuring responses. Thus, if you have any questions, feel free to contact me anytime. 😊
