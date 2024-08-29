import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from function_calling import SaveCSV

storyOutlinePrompt = ChatPromptTemplate.from_template(
    """Here is the English translation of your request:

"Given a page from a document containing various articles, analyze the content and identify sections that are related to crane projects. These projects could be about the purchasing of new cranes, expansion of ports that require new cranes, or modernization of cranes. The page may contain multiple articles or parts of articles. For each input page, call a function to save it as a CSV report. The report should include:

- Summary of the Page: This should explain what the page discusses. If the page contains multiple articles, it should specify that and summarize what each article discusses.
- Include or Exclude: Determine whether the section discusses a crane-related project. If it does, mark it as 'Include'. If it does not, mark it as 'Exclude'.
- Reason: If a section is marked as 'Exclude', provide a brief explanation as to why this was done."
- Articles discussing significant expansions of ports should be included, also if no mention of crane purchases are made
- Modernization and upgrade projects in cranes are always related to the mechanical compontents or Digitization in these processes within cranes. Articles that are for instance discussing tires, wireless networks or fuel types should not be included.
- When in doubt, make sure to include the article.

You have to call the function 'SaveCSV' after analyzing the page,all the parameters are required.


page content:
```
{doc}
```
"""
)


def init_openai(model, key, base):
    return ChatOpenAI(model=model,
                      openai_api_key=key,
                      openai_api_base=base).bind_tools([SaveCSV])


def analyze_page(page_content, oai_model):
    chain = storyOutlinePrompt | oai_model
    result = chain.invoke({"doc": page_content})
    try:
        result = result.additional_kwargs['tool_calls'][0]['function']['arguments']
    except:
        print(result)
        return {"summary": "please check the content manually",
                "include_or_exclude": "Include",
                "reason": "Model not able to analyze the content"}
    return json.loads(result)
