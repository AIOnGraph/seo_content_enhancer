import pandas as pd
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone as pp
import os
from content_updater import clean_scraped_data_using_openai
from langchain_community.vectorstores.pinecone import Pinecone
import requests
import streamlit as st
from bs4 import BeautifulSoup


def extract_urls_from_excel(file_path):
    df = pd.read_excel(file_path)
    try:
        urls = df['URL'].loc[:1]
        list_of_urls = list(urls)
        print(list_of_urls)
        return list_of_urls
    except KeyError as e:
        return None


def text_splitter_and_store_in_db(dict_of_scraped_content, my_bar):
    for url, blog_content in dict_of_scraped_content.items():
        my_bar.progress(60, text="Processing Content ...")
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        document = text_splitter.create_documents(
            texts=[blog_content], metadatas=[{"origin": url}])
        docs = text_splitter.split_documents(document)
        my_bar.progress(60, text="Processing end ...")
        response = store_data_in_pinecone(docs, my_bar)
        return response


def store_data_in_pinecone(document, my_bar):
    my_bar.progress(75, text="Initializing database...")
    index_name = 'blogurlcontent'
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    pp(api_key=st.secrets["PINECONE_API_KEY"])
    Pinecone.from_documents(document, embeddings, index_name=index_name)
    my_bar.progress(100, text="Done ...")
    return "Successfully Uploaded"


def search_similar():
    index_name = 'blogurlcontent'
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    docsearch = Pinecone.from_existing_index(index_name, embeddings)
    query = "https://www.ongraph.com/market-research-software-tools-for-survey-creation/"
    docs = docsearch.similarity_search(query, k=1)
    print(docs[0].page_content)


def crawl_data_using_urlslist(list_of_urls, my_bar):
    dict_of_scraped_content = {}
    print(list_of_urls)
    try:
        for url in list_of_urls:
            print(f"crawling url----{url}")
            response = requests.get(url)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text()
            removed_extraline_from_content = "\n".join(
                line.strip() for line in page_text.splitlines() if line.strip())
            dict_of_scraped_content[url] = removed_extraline_from_content
            my_bar.progress(20, text="Content Crawled Successfully ..")
        return dict_of_scraped_content
    except Exception:
        return None


def process_to_store_data(url, my_bar):
    list_of_url = [url]
    dict_of_scraped_content = crawl_data_using_urlslist(list_of_url, my_bar)
    if dict_of_scraped_content:
        dict_of_cleaned_content = clean_scraped_data_using_openai(
            dict_of_scraped_content, my_bar, url)
        response = text_splitter_and_store_in_db(
            dict_of_cleaned_content, my_bar)
        return response
    else:
        my_bar.progress(20, text="try again ! failed")
        return "failed to upload !!"


def get_content_from_database(url_input_1, my_bar):
    index_name = 'blogurlcontent'
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    docsearch = Pinecone.from_existing_index(index_name, embeddings)
    query = url_input_1
    docs = docsearch.similarity_search(query, k=1)
    st.session_state.spinner_status = "Searching in database"
    print(docs[0].metadata)
    if docs[0].metadata["origin"] == query:
        st.session_state.spinner_status = "Hurray ! Found the content.. "
        my_bar.progress(15, text=st.session_state.spinner_status)
        return docs[0].page_content
    else:
        st.session_state.spinner_status = "Sorry not find anything in Database .. wait "
        my_bar.progress(10, text=st.session_state.spinner_status)
        return None
