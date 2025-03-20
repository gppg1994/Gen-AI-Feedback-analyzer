import pandas as pd
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.tools import PythonREPLTool
from langchain_experimental.agents import create_pandas_dataframe_agent
import json
import streamlit as st
import time
from langchain.agents import AgentType
from langchain.prompts import MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool
import os,glob


OPENAI_API_KEY = "c8d9627e600842eeaa9d1dac896db384"
OPENAI_DEPLOYMENT_NAME = "BuddyAssistChatModel"
OPENAI_EMBEDDING_MODEL_NAME = "EmbeddingModel"
AZURE_OPENAI_ENDPOINT = "https://buddyassistpoc.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2024-05-01-preview"

#For including chat history refer: https://python.langchain.com/v0.1/docs/modules/agents/how_to/custom_agent/

def stream_data(text):
    for letter in text:
        yield letter
        time.sleep(0.02)
        
def chat(agent,chat_message):
    cwd=os.getcwd()
    with st.container(border=True):
        if 'messages' in st.session_state:
            for message in st.session_state.messages:
                with st.chat_message(name='user'):
                    st.markdown(f"<span style='float:right;background-color: coral;'>{message['input']}</span><br>",unsafe_allow_html=True)
                with st.chat_message(name='ai'):
                    st.markdown(f"{message['output']}")
        
        if chat_message is not None:
            try:
                
                with st.chat_message(name='user'):
                    st.write(f"<span style='float:right;background-color: coral;'>{chat_message}</span><br>",unsafe_allow_html=True)
                with st.spinner("Generating response..."):
                
                    ai_msg=agent.invoke(
                        {
                            "input": chat_message
                        }
                    )
                if 'messages' in st.session_state:
                    st.session_state.messages.append(ai_msg)
                else:
                    st.session_state.messages=[]
                    st.session_state.messages.append(ai_msg)

                #st.write(f"<span style='float:right'>{input_msg}</span>",unsafe_allow_html=True)
                with st.chat_message(name='ai'):
                    st.write(stream_data(ai_msg['output']))
                    #st.write(f"{stream_data(ai_msg['output'])}")
                #st.write("</br>",unsafe_allow_html=True)
                    

            except Exception as ex:
                print(str(ex))
                with st.chat_message(name='ai'):
                    st.write("Please rephrase your question and ask again")
                ai_msg={
                    
                        "input": chat_message,
                        "output":"Please rephrase your question and ask again."
                        
                }
                if 'messages' in st.session_state:
                    st.session_state.messages.append(ai_msg)
                else:
                    st.session_state.messages=[]
                    st.session_state.messages.append(ai_msg)
    if "messages" not in st.session_state : 
        st.markdown("<div style='margin-left:30%;margin-top:20%'> <h5> ✨ Chat with your data</span><h5>",unsafe_allow_html=True)
        #input_msg=st.chat_input("Ask anything about the data...")
    # Display chat messages from history on app rerun

        

def main():
        
    st.set_page_config(layout="centered")

    st.markdown("<h3>Insightify</h3>",unsafe_allow_html=True)

    if 'openai_client' not in st.session_state:    
        llm= AzureChatOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=OPENAI_API_KEY,
            azure_deployment=OPENAI_DEPLOYMENT_NAME,
            api_version=AZURE_OPENAI_API_VERSION
        )
        st.session_state.openai_client=llm
    #tools=[PythonREPLTool()]
    if 'data' not in st.session_state:
        st.toast("No data loaded. Redirecting to Home page...")
        st.switch_page('Dashboard.py')
    data=st.session_state.data
    agent = create_pandas_dataframe_agent(st.session_state.openai_client,df=data,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,prefix=f'''You are a digital assistant working on a dataset of customer feedbacks. Answer the question that has been asked, articulately. The answer should be understandable to a normal human being. Evaluate any expresssion if required.''',verbose=True,allow_dangerous_code=True)
    input_msg=st.chat_input("Ask anything about the data...")
    chat(agent=agent,chat_message=input_msg)

if __name__=='__main__':
    main()
