from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from instruction import instruction_For_Bot,instruction_For_Bot_2,instruction_for_cleaning,test_instruction_for_enhancing_blog
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
import pandas as pd
import streamlit as st
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import re

OPEN_AI_API=st.secrets['OPENAI_API_KEY']


class ContentEnhancer(BaseModel):
    changed_content: str = Field(description="thid field contains the updated content")




def clean_content_data(response_after_scrapping):
    response = re.sub(r'http\S+', '', response_after_scrapping[0].page_content, flags=re.MULTILINE)
    print(response)
    return response


def crawl_data(url):
    print("Extracting blog from url")
    loader = AsyncChromiumLoader([url])
    html = loader.load()
    tags_to_extract=["p","h1", "h2", "h3","span"]
    
    bs_transformer = BeautifulSoupTransformer()
    
    docs_transformed = bs_transformer.transform_documents(html,tags_to_extract=tags_to_extract)
        
    st.session_state.spinner_status="crawling done"
    return docs_transformed



def extract_keywords_from_excel(fileName):
    try: 
        data=pd.read_excel(fileName)
        suggestion_data=list(data["Keyword"])
        filtered_data = data[(data['Keyword Difficulty'] < 50) & (data['Volume'] > 30)]
        keywords_list=list(filtered_data["Keyword"])
        
        return keywords_list,suggestion_data
    except Exception as e:
        return list(e)

def compare_contents(blog_1_content,blog_2_content):
    user_data = f"""First Blog is {blog_1_content},Second Blog {blog_2_content}
"""  
    messages = [
    SystemMessage(
        content=instruction_For_Bot
    ),
    HumanMessage(
        content=user_data
    )]
    chat = ChatOpenAI(model="gpt-4",temperature=0.0,api_key=OPEN_AI_API,verbose=True)    
    response=chat(messages)
    return response




def augment_data_using_keywords(blog_1_content,keywords_list,chat):
    user_data = f"""Blog Content = {blog_1_content} and keyword_list={keywords_list}"""  
    messages = [
    SystemMessage(
        content=test_instruction_for_enhancing_blog
    ),
    HumanMessage(
        content=user_data
    )]
    # chat = ChatOpenAI(model="gpt-3.5-turbo-1106",streaming=True,temperature=0.2,api_key=OPEN_AI_API,callbacks=[StreamlitCallbackHandler(response)])    
    chat.invoke(messages)
    
    # return response


def augment_data_using_keywords_test(keywords_list,):
    user_data = f"""Blog Content = "" and keyword_list={keywords_list}"""  
    
    messages = [
    SystemMessage(
        content=instruction_For_Bot_2
    ),
    HumanMessage(
        content=user_data
    )]
    chat = ChatOpenAI(model="gpt-3.5-turbo-1106",temperature=0.2,api_key=OPEN_AI_API)    
    response=chat.invoke(messages)
    
    return response

def cleandata():
    user_data = f"""Blog Content = """  
    
    messages = [
    SystemMessage(
        content=instruction_for_cleaning
    ),
    HumanMessage(
        content=user_data
    )]
    chat = ChatOpenAI(model="gpt-3.5-turbo-1106",temperature=0.2,api_key=OPEN_AI_API)    
    response=chat.invoke(messages)
    
    return response
       
       
 
       
def content_cleaner_and_content_enhancer(user_data_for_cleaning,keywords_list,my_bar):
    
    
    
    user_data_for_cleaning = f"""Blog Content = {user_data_for_cleaning}"""  
    
    
    #PromptTemplate
    clean_content_template=PromptTemplate(input_variables=["instruction_for_cleaning","user_data_for_cleaning"],template="{instruction_for_cleaning} {user_data_for_cleaning}")
    
    
    parser = JsonOutputParser(pydantic_object=ContentEnhancer)

    
    enhance_content_template=PromptTemplate(input_variables=["test_instruction_for_enhancing_blog","user_data_for_enhancing"],template="{test_instruction_for_enhancing_blog} {user_data_for_enhancing}",partial_variables={"format_instructions": parser.get_format_instructions()})
    
    
    #llm model
    llm_model = ChatOpenAI(model="gpt-4-0613",temperature=0.2,api_key=OPEN_AI_API)
    #chain
    clean_content_chain=LLMChain(llm=ChatOpenAI(model="gpt-3.5-turbo-1106",temperature=0.2,api_key=OPEN_AI_API),prompt=clean_content_template,verbose=True)
   
    cleaned_content=clean_content_chain.run(instruction_for_cleaning=instruction_for_cleaning,user_data_for_cleaning=user_data_for_cleaning)
    st.session_state.spinner_status="Content Cleaned"
    my_bar.progress(50,text=st.session_state.spinner_status)
    user_data_for_enhancing =f"""Blog Content = {cleaned_content} and keyword_list={keywords_list}"""  
    
    enhance_content_chain = enhance_content_template | llm_model | parser 
    
    st.session_state.spinner_status="Content Updating ..."
    my_bar.progress(60,text=st.session_state.spinner_status)
    l=enhance_content_chain.stream({"test_instruction_for_enhancing_blog": test_instruction_for_enhancing_blog,"user_data_for_enhancing":user_data_for_enhancing})
    return l

       