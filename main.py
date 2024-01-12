import streamlit as st
from streamlit_tags import st_tags
from content_updater import crawl_data,content_cleaner_and_content_enhancer,extract_keywords_from_excel
import time
st.title("Blog Enhancer")
if "spinner_status" not in st.session_state:
    st.session_state.spinner_status ="Initializing ..."
    st.session_state.tokken=None
home,secrets  = st.tabs(["HOME",'Secrets'])

with st.sidebar:
    uploadExcel=st.file_uploader(label='**Upload Your Excel file here!**',type=['xlsx'],)
    if uploadExcel is not None:
        keywords,suggestions=extract_keywords_from_excel(uploadExcel)
        list_keyword = st_tags(
            label='Enter KeyWords',
            text='',
            value=keywords,
            suggestions=suggestions,
            maxtags=20,
            key='3')   
    
    

def func():
    url_input_1 = st.text_input(label="Extract Data",placeholder='Paste Blog Url Here',key="text_input_1")
    if st.button("Start Updating Blog",key="Blog_Updater"):
        my_bar=st.progress(0,text=st.session_state.spinner_status)
        my_bar.progress(10,text="crawling start....")
        scrap_content_response=crawl_data(url_input_1)
        my_bar.progress(20,text=st.session_state.spinner_status)
        if scrap_content_response[0].page_content:
            my_bar.progress(25,text="Cleaning Content ...")
            response=content_cleaner_and_content_enhancer(scrap_content_response,list_keyword,my_bar)
            time.sleep(0.5)
            with st.container(border=True):
                my_bar.progress(90,text="Writing ..")    
                placeholder=st.empty()
                for chunk in response:
                    if bool(chunk):
                        time.sleep(0.02)
                        placeholder.markdown(chunk["changed_content"] + "▌")
                my_bar.progress(100,text="Succesfully Done")
        else:
            my_bar.progress(0,text="Failed ! Try again .")
            st.write("Content Not Found")
        
        
            
    
    
if __name__=="__main__":

    with secrets: 
        tokken=st.text_input("ENTER YOUR TOKEN")
        st.session_state.tokken=tokken
    with home:
        print(st.session_state.tokken,111111111111)
        print(st.secrets['TOKKEN'])
        print(type(st.session_state.tokken), type(st.secrets['TOKKEN']))
        if st.session_state.tokken is None or st.session_state.tokken=="" :
            st.warning('Please enter token in secret tab!!!',icon="⚠️") 
            
        elif st.session_state.tokken != st.secrets['TOKKEN']:
            st.error('INVALID TOKEN',icon="🚨" )
            
            
        elif st.session_state.tokken == st.secrets['TOKKEN']:
            func()
            
               
        
                
            
   
