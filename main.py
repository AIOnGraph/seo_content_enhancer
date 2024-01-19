import streamlit as st
from streamlit_tags import st_tags
from content_updater import crawl_data,content_cleaner_and_content_enhancer,extract_keywords_from_excel
import time

st.markdown("""
    <style>
        .streamlit-slider { width: 500px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("Blog Enhancer")
if "spinner_status" not in st.session_state:
    st.session_state.spinner_status ="Initializing ..."
    st.session_state.tokken=None
    
    
if "keyword_list" not in st.session_state:
    st.session_state.keyword_list =[]
    
home,secrets  = st.tabs(["HOME",'Secret Key'])

with st.sidebar:
    
    
    keyword_difficulty_score=st.slider("**Keyword Difficulty Score**", 0, 100,value=50)
    keyword_volume_score=st.slider("**Keyword Volume Score**", 0, 100 ,value=30)
    uploadExcel=st.file_uploader(label='**Upload Your Excel file here!**',type=['xlsx'],help='**file must contain keys** :red[*Keyword,Keyword Difficulty,Volume.*]')
    if uploadExcel is not None:
        keywords=extract_keywords_from_excel(uploadExcel,keyword_difficulty_score,keyword_volume_score)
        if keywords:
            list_keyword = st_tags(
            label='**Enter KeyWords To Include**',
            text='',
            value=keywords[0],
            suggestions=keywords[1],
            maxtags=20,
            key='3')
            st.session_state.keyword_list  =list_keyword 
        else:
            st.warning('Invalid Format!',icon="🚨")    
    
    

def func():
    url_input_1 = st.text_input(label="Extract Data",placeholder='Paste Blog Url Here',key="text_input_1")
    if st.button("Start Updating Blog",key="Blog_Updater"):
        if st.session_state.tokken == st.secrets['TOKKEN']:
            if st.session_state.keyword_list:    
                my_bar=st.progress(0,text=st.session_state.spinner_status)
                my_bar.progress(10,text="crawling start....")
                scrap_content_response=crawl_data(url_input_1)
                my_bar.progress(20,text=st.session_state.spinner_status)
                if scrap_content_response:
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
                        # st.snow()       
                        my_bar.progress(100,text="Succesfully Done")
                else:
                    my_bar.progress(0,text="Failed ! Try again .")
            else: 
                st.warning("Please Upload File to extract Keywords",icon="⚠️")
        elif st.session_state.tokken is None or st.session_state.tokken=="" :
            st.warning('Please enter token in secret tab!!!',icon="⚠️") 
        elif st.session_state.tokken != st.secrets['TOKKEN']:
            st.error('INVALID TOKEN',icon="🚨" )
            
        
    
    
if __name__=="__main__":

    with secrets: 
        tokken=st.text_input("ENTER YOUR TOKEN",type="password")
        st.session_state.tokken=tokken
        if st.session_state.tokken is None or st.session_state.tokken=="" :
            st.warning('Please enter token in secret tab!!!',icon="⚠️")
        elif st.session_state.tokken != st.secrets['TOKKEN']:
            st.error('INVALID TOKEN',icon="🚨" )
        elif st.session_state.tokken == st.secrets['TOKKEN']:
            # st.balloons()
            st.warning(":green[**Verified Succesfully**] ")
    with home:
        func()

          
               
        
                
            
   
