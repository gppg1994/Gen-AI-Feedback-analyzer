from openai import AzureOpenAI
import pandas as pd
import json
from io import StringIO
import streamlit as st
import altair as alt
import datetime as dt
import os

OPENAI_API_KEY = "c8d9627e600842eeaa9d1dac896db384"
OPENAI_DEPLOYMENT_NAME = "BuddyAssistChatModel"
OPENAI_EMBEDDING_MODEL_NAME = "EmbeddingModel"
AZURE_OPENAI_ENDPOINT = "https://buddyassistpoc.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2024-05-01-preview"

client = AzureOpenAI(
    api_key=OPENAI_API_KEY,  
    api_version= AZURE_OPENAI_API_VERSION,
    azure_endpoint =AZURE_OPENAI_ENDPOINT
    )

def process_feedback(df):
    # Check if "Feedback" column is in the DataFrame
    if 'Feedback' not in df.columns:
        raise ValueError('No "Feedback" column in the DataFrame')
    # Remove newline/tab characters
    df['Feedback'] = df['Feedback'].replace('\n',' ', regex=True)
    df['Feedback'] = df['Feedback'].replace('\t',' ', regex=True)
    # Removing any special characters
    df['Feedback'] = df['Feedback'].str.replace("[^\w\s]",' ')
    return df

def getResponse(_query):
    prompt_file=open(r"Input Data/Prompt.txt")
    system_prompt=prompt_file.read()
    
    examples='''One example is given below:
Input:

"The utility's quick response to outages is commendable, ensuring minimal disruption to daily activities. It's reassuring to know that power restoration is a top priority, contributing to a sense of reliability and trust among customers."|"Billing statements are straightforward and transparent, making it easy to understand charges and manage finances effectively. This clarity fosters trust and satisfaction among customers, eliminating the frustration often associated with complex billing systems."|"The company's efforts in community engagement and education initiatives appear limited or sporadic. While occasional outreach events or energy-saving tips may be provided, there is a lack of sustained and impactful programs that empower customers to understand and manage their energy usage better. This absence of comprehensive education and engagement efforts not only hinders customer awareness but also misses an opportunity to build stronger relationships and loyalty within the community."|"Customer service representatives consistently demonstrate professionalism and efficiency, addressing queries and concerns with empathy and effectiveness. This level of service enhances customer satisfaction and loyalty, fostering positive relationships between the utility and its clientele."|"No issues with the electrical service, been using it for years."


Output:

The utility's quick response to outages is commendable, ensuring minimal disruption to daily activities. It's reassuring to know that power restoration is a top priority, contributing to a sense of reliability and trust among customers.;1. Quick response to outages;Electric Services;Service Quality;Positive
Billing statements are straightforward and transparent, making it easy to understand charges and manage finances effectively. This clarity fosters trust and satisfaction among customers, eliminating the frustration often associated with complex billing systems.;1. Straightforward billing statements;General;Affordability;Positive
The company's efforts in community engagement and education initiatives appear limited or sporadic. While occasional outreach events or energy-saving tips may be provided, there is a lack of sustained and impactful programs that empower customers to understand and manage their energy usage better. This absence of comprehensive education and engagement efforts not only hinders customer awareness but also misses an opportunity to build stronger relationships and loyalty within the community.;1. Limited Customer engagement   2. Lack of creation of customer awareness;General;General;Negative
Customer service representatives consistently demonstrate professionalism and efficiency, addressing queries and concerns with empathy and effectiveness. This level of service enhances customer satisfaction and loyalty, fostering positive relationships between the utility and its clientele.;1. Professional customer service   2. Queries and concerns addressed with empathy and effectiveness   3. Promotes customer loyalty;General;Customer Service and Communication;Positive
No issues with the electrical service, been using it for years.;No issues with electrical service;Electric Services;General;Neutral
'''
    response=client.chat.completions.create(
        model=OPENAI_DEPLOYMENT_NAME,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "system", "content": examples},
        {"role": "user", "content": _query}],    
        temperature=0
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content
#st.set_page_config(layout="wide")
def main():
    st.set_page_config(layout="wide")
    st.markdown("<h2>Insightify</h2>",unsafe_allow_html=True)
    res=pd.DataFrame(columns=['Feedback','Feedback Summary','Department','Category','Sentiment'])
    uploaded_file = st.file_uploader("Choose a file") #create upload feature
    if 'data' not in st.session_state:
        df_full=pd.DataFrame()
    else:
        df_full=st.session_state.data
    if uploaded_file is not None:
        
        if  'csv' in uploaded_file.type:        
            df_input=pd.read_csv(uploaded_file) #read the uploaded file
        elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in uploaded_file.type:
            df_input=pd.read_excel(uploaded_file)
        #df_input=process_feedback(df_input)
        df_feedback=pd.DataFrame(columns=df_input.columns.to_list())
        df_feedback["Feedback"]=['\"'+df_input['Feedback'][i]+'\"' for i in range(0, len(df_input)) ] #enclosing every feedback with ""
        #creating css styling for div items
        st.markdown('''<style>
                    div.stMarkdown
                    {
                        line-height:1;
                        font-size:5%;
                        word-break: break-all;
                        font: Calibri;
                        padding-top: -5px;
                    }
                    </style>
                    ''',unsafe_allow_html=True)
        
        
        feedback_chunks = [df_feedback['Feedback'][i:i+5].tolist() for i in range(0, len(df_feedback), 5)]
        my_bar = st.progress(0)
        placeholder = st.empty()
        
        placeholder.text('Loading data...')
        percent_complete=0
        #Progress bar
        for batch in feedback_chunks:
            #getting genAI response
            df=pd.read_csv(StringIO(getResponse("|".join(batch))), sep=';',names=('Feedback','Feedback Summary','Department','Category','Sentiment'))
            res=pd.concat([res,df])
            my_bar.progress(percent_complete + (len(res)/(len(feedback_chunks)*5)))

        placeholder.empty()
        my_bar.empty()
        #appending additional columns to the response generated by genAI
        res=res.reset_index()
        #res.to_excel("test_output.xlsx")
        res['Age']=[df_input.loc[list(df_input['Feedback']).index(res['Feedback'][i].strip()),'Age'] for i in range(0,len(res))]
        res['Location']=[df_input.loc[list(df_input['Feedback']).index(res['Feedback'][i].strip()),'Location'] for i in range(0,len(res))]
        res['Source of feedback']=[df_input.loc[list(df_input['Feedback']).index(res['Feedback'][i].strip()),'Source of feedback'] for i in range(0,len(res))]
        res['Timestamp']=[df_input.loc[list(df_input['Feedback']).index(res['Feedback'][i].strip()),'Timestamp'] for i in range(0,len(res))]
        res=res[['Timestamp','Feedback','Feedback Summary','Age','Location','Source of feedback','Department','Category','Sentiment']]
        res.to_csv("Output data\output data.csv",index=None) #storing to output
        df_full=pd.concat([df_full,res])
        st.session_state.data=df_full
        df_full.to_excel("Input Data\Collection.xlsx",sheet_name="Collection",index=None)
        st.session_state['data']=df_full
        st.session_state['is_uploaded']=True
        if 'key' in st.session_state:
            del st.session_state.key      
            
    if os.path.exists("Output data\output data.csv") :
        res=pd.read_csv("Output data\output data.csv")
        
        if 'upload_data' not in st.session_state:
            st.session_state.upload_data=res
        
        st.dataframe(res,hide_index=True)
        # res['count']=1
        # total_counts = res.groupby('Category')['count'].transform('sum')
        # res['NormalizedCount'] = (res['count'] / total_counts)*100
        # color_scale = alt.Scale(
        #         domain=[
        #             "Positive",
        #             "Negative",
        #             "Neutral"        ],
        #         range=["#0068C9", "#FF2B2B", "#83C9FF"] #setting custom colours for items
        #     )
        # chart=alt.Chart(res).mark_bar().encode(
        #     x=alt.X('Category:N',),
        #     y=alt.Y('count:Q'),
        #     color=alt.Color('Sentiment:N',scale=color_scale)
            
        # )
        # arr_categories=res['Category'].unique()
        # idx=0
        # #creating two separate rows for categories. each category will be in the form of tiles
        # row1=st.columns(int(len(res['Category'].unique())/2))
        # row2=st.columns(int(len(res['Category'].unique())/2))
        
        # #populating positive, negative, neutral counts in each tile
        # for col in row1+row2:
        #     tile=col.container(border=True)    
        #     tile.write(arr_categories[idx])
        #     tile.markdown(f'''<p style='font-size:25px;color:#0068C9;'>{len(res[(res['Category']==arr_categories[idx]) & (res['Sentiment']=='Positive')])}
        #                 <span style='font-size:25px;color:#83C9FF;margin-left:70px'>{len(res[(res['Category']==arr_categories[idx]) & (res['Sentiment']=='Neutral')])}</span>
        #                 <span style='font-size:25px;color:#FF2B2B;float:right'>{len(res[(res['Category']==arr_categories[idx]) & (res['Sentiment']=='Negative')])}</span></p>''',unsafe_allow_html=True)
        #     idx+=1
        # st.markdown('''
        #             </br></br></br>
                    
        #             ''',unsafe_allow_html=True) #adding space
        #st.altair_chart(chart,use_container_width=True)#plotting stacked chart

        
        #creating tiles for top performers
        idx=0
        st.markdown("<br><br>",unsafe_allow_html=True)
        row_a,row_b,row_c=st.columns(3)
        row1,row2=row_a.columns(2)
        with row1.container(border=True):
            st.markdown("Total feedbacks processed")
            st.markdown(f"### {len(res)}")
         
        with row2.container(border=True):
            st.markdown("Positive feedbacks are :thumbsup:")
            st.markdown(f"### {len(res[res['Sentiment']=='Positive'])/len(res)*100:0.0f}%")
            st.markdown(f"Positive feedbacks account for {len(res[res['Sentiment']=='Positive'])} out of total {len(res)}")
        row1,row2=row_b.columns(2)
        with row1.container(border=True):
            st.markdown("Negative feedbacks are :thumbsdown:")
            st.markdown(f"### {len(res[res['Sentiment']=='Negative'])/len(res)*100:0.0f}%")
            st.markdown(f"Negative feedbacks account for {len(res[res['Sentiment']=='Negative'])} out of total {len(res)}")
        
        with row_c.container(border=True):
            st.markdown("### Feedback by department")
            df_deptRank=res.groupby('Department').size().reset_index(name='Count')
            df_deptRank=df_deptRank.rename(columns={'index':'Department'})
            st.dataframe(df_deptRank,
                        hide_index=True,
                        column_config={
                        "Department": st.column_config.TextColumn(
                            "Department",
                        ),
                        "Count": st.column_config.ProgressColumn(
                            "Count",
                            format="%f",
                            min_value=0,
                            max_value=len(res)
                        )}
            )
        
        with row2.container(border=True):
            st.markdown("This time's best performing category :trophy:")
            print(res[(res['Sentiment']=='Positive') | (res['Sentiment']=='Neutral')].groupby('Category').size().idxmax())
            st.markdown(f"### {res[(res['Sentiment']=='Positive') | (res['Sentiment']=='Neutral')].groupby('Category').size().idxmax()}")
            st.markdown(f"{res[(res['Sentiment']=='Positive') | (res['Sentiment']=='Neutral')].groupby('Category').size().max()/len(res)*100:.0f}% positive impressions!")
        st.write("</br></br>",unsafe_allow_html=True)
        st.session_state['is_uploaded']=True
        
    #chat placeholder. Integrate Llama index code here

if __name__=='__main__':
    main()
