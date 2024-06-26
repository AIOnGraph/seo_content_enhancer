from instruction import instruction_for_cleaning_test, instruction_for_cleaning, instruction_for_enhancing_blog
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import pandas as pd
import streamlit as st
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re
import requests
from bs4 import BeautifulSoup

OPEN_AI_API = st.secrets['OPENAI_API_KEY']


class ContentEnhancer(BaseModel):
    changed_content: str = Field(
        description="thid field contains the updated content")




def crawl_data(url):
    try:
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        page_text = soup.get_text()
        remove_extraline_from_content = "\n".join(
            line.strip() for line in page_text.splitlines() if line.strip())
        st.session_state.spinner_status = "crawling done"
        return remove_extraline_from_content
    except Exception as e:
        return None


def extract_keywords_from_excel(fileName, keyword_difficulty_score, keyword_volume_score):
    try:
        data = pd.read_excel(fileName)
        suggestion_data = data["Keyword"]
        filtered_data = data[(data['Keyword Difficulty'] < keyword_difficulty_score) & (
            data['Volume'] > keyword_volume_score)]
        keywords_list = filtered_data["Keyword"]
        return [list(keywords_list), list(suggestion_data)]
    except KeyError as e:
        return None





def clean_scraped_data_using_openai(dict_of_scraped_content, my_bar, url):
    content_data = dict_of_scraped_content[url]
    user_data = f"""Blog Content = {content_data}"""
    my_bar.progress(25, text="Cleaning Content")
    messages = [
        SystemMessage(
            content=instruction_for_cleaning_test
        ),
        HumanMessage(
            content=user_data
        )]
    short_llm = ChatOpenAI(
        model="gpt-4-0613", temperature=0.2, api_key=OPEN_AI_API)
    long_llm = ChatOpenAI(
        model="gpt-4-32k", temperature=0.2, api_key=OPEN_AI_API)
    llm = short_llm.with_fallbacks([long_llm])
    response = llm.invoke(messages)
    dict_of_scraped_content[url] = response.content
    my_bar.progress(35, text="Content Cleaned")
    return dict_of_scraped_content


def content_cleaner_and_content_enhancer(blog_content_from_db, user_data_for_cleaning, keywords_list, my_bar, update_content_only):

    if update_content_only:
        response = content_enhancer(blog_content_from_db, keywords_list)
        return response
    else:

        my_bar.progress(25, text="Cleaning Content ...")
        user_data_for_cleaning = f"""Blog Content = {user_data_for_cleaning}"""

        # PromptTemplate
        clean_content_template = PromptTemplate(input_variables=[
                                                "instruction_for_cleaning", "user_data_for_cleaning"], template="{instruction_for_cleaning} {user_data_for_cleaning}")

        parser = JsonOutputParser(pydantic_object=ContentEnhancer)

        enhance_content_template = PromptTemplate(input_variables=["instruction_for_enhancing_blog", "user_data_for_enhancing"],
                                                  template="{instruction_for_enhancing_blog} {user_data_for_enhancing}", partial_variables={"format_instructions": parser.get_format_instructions()})

        # llm model
        llm_model = ChatOpenAI(
            model="gpt-4-0613", temperature=0.2, api_key=OPEN_AI_API)
        # chain
        clean_content_chain = LLMChain(llm=ChatOpenAI(
            model="gpt-3.5-turbo-1106", temperature=0.2, api_key=OPEN_AI_API), prompt=clean_content_template)

        cleaned_content = clean_content_chain.run(
            instruction_for_cleaning=instruction_for_cleaning, user_data_for_cleaning=user_data_for_cleaning)

        st.session_state.spinner_status = "Content Cleaned"
        my_bar.progress(50, text=st.session_state.spinner_status)
        user_data_for_enhancing = f"""Blog Content = {cleaned_content} and keyword_list={keywords_list}"""

        enhance_content_chain = enhance_content_template | llm_model | parser

        st.session_state.spinner_status = "Content Updating ..."
        my_bar.progress(60, text=st.session_state.spinner_status)
        stream_object = enhance_content_chain.stream(
            {"instruction_for_enhancing_blog": instruction_for_enhancing_blog, "user_data_for_enhancing": user_data_for_enhancing})
        return stream_object


def content_enhancer(cleaned_content_data_from_db, keywords_list):
    parser = JsonOutputParser(pydantic_object=ContentEnhancer)
    enhance_content_template = PromptTemplate(input_variables=["instruction_for_enhancing_blog", "user_data_for_enhancing"],
                                              template="{instruction_for_enhancing_blog} {user_data_for_enhancing}", partial_variables={"format_instructions": parser.get_format_instructions()})
    user_data_for_enhancing = f"""Blog Content = {cleaned_content_data_from_db} and keyword_list={keywords_list}"""
    llm_model = ChatOpenAI(
        model="gpt-4-0613", temperature=0.2, api_key=OPEN_AI_API)
    enhance_content_chain = enhance_content_template | llm_model | parser
    stream_object = enhance_content_chain.stream(
        {"instruction_for_enhancing_blog": instruction_for_enhancing_blog, "user_data_for_enhancing": user_data_for_enhancing})
    return stream_object
