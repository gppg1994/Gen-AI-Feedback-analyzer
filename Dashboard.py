from openai import AzureOpenAI
import pandas as pd
import json
from io import StringIO
import streamlit as st
import altair as alt
import time
import calendar
import datetime as dt
import matplotlib.pyplot as plt
import plotly.express as px
from collections import OrderedDict
import calendar
import os
import plotly.graph_objects as go


OPENAI_API_KEY = "4f4ffeb62271468f9ab3586cfe712d02"
OPENAI_DEPLOYMENT_NAME = "deploy-gpt4"
OPENAI_EMBEDDING_MODEL_NAME = "EmbeddingModel"
MODEL_NAME = "gpt-35-turbo"
# openai.api_type = "azure"
AZURE_OPENAI_ENDPOINT = "https://testpoc123.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
# openai.api_key = OPENAI_API_KEY

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
    df['Feedback'] = df['Feedback'].str.replace('[^\w\s]',' ')
    return df

def getResponse(_query):

    system_prompt='''You are a data analyst. You are provided with some customer feedback data. Analyse the data and give a brief and concise
    analysis of the data. Give insightful inferences by analysing the data. Give your answers in points as well as paragraphs wherever applicable.
    Do not add anything on your own. The analysis should be strictly limited to the dataset given.
    Give suitable suggetsions/opinions at the end.'''
    
    response=client.chat.completions.create(
        model=OPENAI_DEPLOYMENT_NAME,
        messages=[{"role":"system","content":system_prompt},{"role":"user","content":str(_query) }],
        temperature=0.3
        
    )
    
    return response.choices[0].message.content

#st.set_page_config(layout="wide")

def generate_smart_response(data):
    if 'key' not in st.session_state:
                with st.spinner("Loading..."):
                    intg_resp=getResponse(data[['Timestamp','Feedback Summary','Department','Category','Sentiment','Source of feedback','Age','Location']])
                
                    #intg_resp=getResponse(data)
                    st.session_state["key"]=intg_resp
                    
    else:
        intg_resp=st.session_state["key"]
    
    return intg_resp

def main():
    
       
    st.set_page_config(layout="wide")
    st.write("<h2>Insightify</h2>",unsafe_allow_html=True)
    placeholder=st.columns(6)[5]
    home,st_analysis,catg_analysis,dept_analysis,intg_analysis=st.tabs(["Home","Sentiment Analysis","Category Analysis","Department Analysis"," :sparkles: Intelligent Analysis"])
    if os.path.exists(r"Input Data/Collection.xlsx"):
        if 'data' not in st.session_state:        
            st.session_state.data=pd.read_excel("Input Data\Collection.xlsx")
        all_data=st.session_state.data
        data=all_data
        
        data['month'] = pd.to_datetime(data['Timestamp'], errors='coerce').dt.month
        data['month_name'] = pd.to_datetime(data['Timestamp'], errors='coerce').dt.month_name()
        month_names=[calendar.month_name[i] for i in range(1,13)]
        category_list=["Service Quality","Customer Service and Communication","Compliance and Security","Affordability","Environmental Responsibility","Community Relationship"]               
        sentiment_values=['Positive', 'Negative', 'Neutral']
        #st.session_state.data=data
        with home:
            col1,col2,col3=st.columns(3)
            placeholder=col1.container(border=True)

            col1_1,col1_2=placeholder.columns(2)
            col1_1.write("Total Feedbacks Received:raised_hand_with_fingers_splayed:")
            col1_1.markdown(f"<h1>{len(data)}</h1>",unsafe_allow_html=True)
            pie_values={}
            pie_values={
                        'Sentiment':['Positive','Negative','Neutral'],
                        'count':[len(data[data['Sentiment']=='Positive']),len(data[data['Sentiment']=='Negative']),len(data[data['Sentiment']=='Neutral'])]
            }
            df_pievalues=pd.DataFrame(data=pie_values)
            #print(df_pievalues)
            fig=px.pie(pie_values,values='count', 
                            names='Sentiment',
                            color='Sentiment',
                            color_discrete_map={
                                            'Neutral':'#83C9FF',
                                            'Negative':'#FF2B2B',
                                            'Positive': '#0068C9'
                                            } ,
                            hole=0.5,
                            width=60
                            )   
            fig.update_layout(showlegend=True,height=305,margin=dict(l=0, r=0, t=1, b=0),legend=dict(orientation="h"))
            col1_2.plotly_chart(fig,use_container_width=True)
            
            placeholder=col2.container(border=True)
            df_dept=data[((data['Sentiment']=='Positive') | (data['Sentiment']=='Neutral')) & (data['Department']!='General')]
            df_dept_all=data[((data['Sentiment']=='Positive') | (data['Sentiment']=='Neutral'))]
           
            col2_1,col2_2=placeholder.columns(2)
            col2_1.write("Best performing department:trophy:",unsafe_allow_html=True)
            col2_1.markdown(f"<h4>{df_dept.groupby('Department').size().idxmax()}</h4>",unsafe_allow_html=True)
            col2_1.write(f"{round(max((df_dept.groupby('Department').size()))/len(df_dept_all)*100)}%* positive impressions!")
            pie_values= df_dept_all.groupby('Department').size().reset_index(name='count')
            fig=px.pie(pie_values,values='count', 
                            names='Department',
                            color='Department',
                            hole=0.5,
                            width=60
                            )   
          
            col2_1.write(f"<p style='line-height:12px'><br><br><br><br><br><span style='font-size:12px;'>*There are around {round((len(df_dept_all[df_dept_all['Department']=='General'])/len(df_dept_all))*100)}% data categorised as <strong>General</strong></span></p>",unsafe_allow_html=True)
            
            max_id=df_dept.groupby('Department').size().values.argmax()
            if df_dept_all.groupby('Department').size().reset_index(name='count').at[max_id,'Department']=='General':
                max_id=df_dept.groupby('Department').size().values.argmax()
            pull_array=[0]*len(pie_values)
            pull_array[max_id]=0.2
            fig=go.Figure(data=[go.Pie(labels=pie_values['Department'].to_list(),values=pie_values['count'].to_list(),pull=pull_array)])
            fig.update_layout(showlegend=True,height=305,margin=dict(l=0, r=0, t=1, b=0),legend=dict(orientation="h"))
            col2_2.plotly_chart(fig,use_container_width=True)
            
            placeholder=col3.container(border=True)
            df_category=data[((data['Sentiment']=='Positive') | (data['Sentiment']=='Neutral')) & (data['Category']!='General')]
            df_catg_all=data[((data['Sentiment']=='Positive') | (data['Sentiment']=='Neutral'))]
            col3_1,col3_2=placeholder.columns(2)
            col3_1.write("Our best service:star:",unsafe_allow_html=True)
            col3_1.markdown(f"<h4>{df_category.groupby('Category').size().idxmax()}</h4>",unsafe_allow_html=True)
            col3_1.write(f"{round(max(df_category.groupby('Category').size())/len(df_catg_all)*100)}%* positive impressions!")
            pie_values= df_catg_all.groupby('Category').size().reset_index(name='count')
            fig=px.pie(pie_values,values='count', 
                            names='Category',
                            color='Category',
                            hole=0.5,
                            width=60
                            )   
            df_max_cat=df_catg_all.groupby('Category').size().reset_index(name='count').sort_values(by='count',ascending=False).head(2)
            print(df_catg_all.groupby('Category').size().values.argmax())
            max_id=df_catg_all.groupby('Category').size().values.argmax()
            if df_catg_all.groupby('Category').size().reset_index(name='count').at[max_id,'Category']=='General':
                max_id=df_category.groupby('Category').size().values.argmax()
            #print(df_catg_all.groupby('Category').size().reset_index(name='count').sort_values(by='count',ascending=False))
            pull_array=[0]*len(pie_values)
            pull_array[max_id]=0.2
            fig=go.Figure(data=[go.Pie(labels=pie_values['Category'].to_list(),values=pie_values['count'].to_list(),pull=pull_array)])
            fig.update_layout(showlegend=True,height=305,margin=dict(l=0, r=0, t=1, b=0),legend=dict(orientation="h"))
            col3_2.plotly_chart(fig,use_container_width=True)
            col3_1.write(f"<p style='line-height:12px'><br><br><br><br><br><br><br><br><br><span style='font-size:12px;'>*There are around {round((len(df_catg_all[df_dept_all['Category']=='General'])/len(df_catg_all))*100)}% data categorised as <strong>General</strong></span></p>",unsafe_allow_html=True)
            
            col1,col2=st.columns(2)
            
            placeholder=col1.container(border=True)
            col1_1,col1_2=placeholder.columns(2)
            df_feedback_source=data.groupby('Source of feedback').size()
            
            col1_1.write("Customers reached out to us most via:wave:")
            col1_1.markdown(f"<h4>{df_feedback_source.idxmax()} </h4>",unsafe_allow_html=True)
            col1_1.write(f"{(max(df_feedback_source)/len(data))*100:.0f} % feedbacks received!")
            fig = go.Figure(go.Indicator(
                    mode = "gauge",                    
                    #value = round(max(df_feedback_source)/len(data)*100),
                    gauge={
                        'borderwidth': 0.5,
                        'bar': {'color': "rgb(255, 171, 171)",'thickness':0.75},
                        'bordercolor': "rgb(255, 171, 171)",
                        'bgcolor': "#F2F2F2",
                        
                        'axis':{'range':[None,100],'tickcolor': "white"},
                    },
                    domain = {'x': [0, 1], 'y': [0, 1]}
            ))
            fig.update_traces(value = round(max(df_feedback_source)/len(data)*100))
            fig.update_layout(margin=dict(l=0, r=15, t=20, b=5),height=130)
            col1_2.plotly_chart(fig,use_container_width=True)
            
            
            col2_1,col2_2=col2.columns(2)
            placeholder=col2_1.container(border=True)
            placeholder.write("Most feedback received from:round_pushpin:")  
            print(data.groupby('Location').value_counts())        
            sats_loc=data.groupby('Location').size().idxmax()
            placeholder.markdown(f"<h4>{sats_loc}</h4>",unsafe_allow_html=True)
            placeholder.write(f"Customers are mostly discussing about our <b>{data[data['Location']==sats_loc].groupby('Category').size().idxmax()}</b>",unsafe_allow_html=True)
            placeholder=col2_2.container(border=True)
            placeholder.write("Most active user base are of age	:family:")
            print("Age group: Size")
            print(data.groupby('Age').size())
            print("Age group: value_counts")
            print(data.groupby('Age').value_counts())
            age_grp=data.groupby('Age').size().reset_index(name='count').sort_values(by=['count','Age'],ascending=False).reset_index()
            arr_agegrp=[age_grp['Age'][1],age_grp['Age'][0]]
            arr_agegrp.sort(reverse=True)
            placeholder.markdown(f"<h4>{arr_agegrp[1]}-{arr_agegrp[0]} years</h4>",unsafe_allow_html=True)
            #placeholder.write(f"Customers are mostly unhappy with our <b>{data[data['Location']==unsats_loc].groupby('Category').size().idxmax()}</b>",unsafe_allow_html=True)        
        with intg_analysis:
            #st.markdown("<h5>Intelligent Analysis</h5>",unsafe_allow_html=True)
            placeholder=st.container(border=True)
            placeholder.write(":sparkles:")
            feedback_chunks = [data[i:i+5] for i in range(0, len(data), 5)]
            intg_resp=generate_smart_response(data)
            placeholder.markdown(f"<i>{intg_resp}</i>",unsafe_allow_html=True)              
        
        with catg_analysis:
            placeholder=st.empty()
                
            with placeholder.container(border=True):
                st.markdown("<h3>Category wise Feedback Trends</h2>",unsafe_allow_html=True)
                col1,col2=st.columns(2)
                color_scale = alt.Scale(
                    domain=[
                        "Positive",
                        "Negative",
                        "Neutral"        ],
                    range=["#0068C9", "#FF2B2B", "#83C9FF"] #setting custom colours for items
                )
                catg_option=col1.selectbox(label="Select category",options=category_list,placeholder=category_list[0],index=None)
                #st.write(data[data['Sentiment']=='Positive'])
                
                if catg_option==None:
                    catg_df=data[(data['Category']==category_list[0])].groupby(['month_name', 'Sentiment']).size().reset_index(name='count') 
                else:
                    catg_df=data[(data['Category']==catg_option)].groupby(['month_name', 'Sentiment']).size().reset_index(name='count') 
                
                all_combinations = [(m, cat) for m in month_names for cat in sentiment_values]
                missing_data = pd.DataFrame(all_combinations, columns=['month_name', 'Sentiment'])
                catg_df = pd.merge(catg_df, missing_data, on=['month_name', 'Sentiment'], how='right').fillna(0)
                
                color_scale = alt.Scale(
                    domain=[
                        "Positive",
                        "Negative",
                        "Neutral"        ],
                    range=["#0068C9", "#FF2B2B", "#83C9FF"] #setting custom colours for items
                )
                
                chart=alt.Chart(catg_df).mark_line().encode(
                    x=alt.X('month_name:O', axis=alt.Axis(title='Month', labels=True), scale=alt.Scale(domain=[str(m) for m in month_names]), sort=list(calendar.month_name[1:])),
                    y=alt.Y('count:Q', axis=alt.Axis(title=r'Count of Feedbacks')),
                    color=alt.Color('Sentiment:N',scale=color_scale)
                )             
                st.altair_chart(chart,use_container_width=True)  
                
            with st.container(border=True):
                st.markdown("<h3>Feedback Trends</h2>",unsafe_allow_html=True)
                row0=st.columns(3)
                row1=st.columns(3)
                row2=st.columns(3)
                select_month=row0[0].selectbox(label="Select month",options=month_names,placeholder=calendar.month_name[dt.date.today().month],index=None)
                if select_month==None:
                    select_month=calendar.month_name[dt.date.today().month]
                idx=0
                for c in row1:
                    c.markdown(category_list[idx])
                    filtered_data=data[(data['month_name']==select_month) & (data['Category']==category_list[idx])]
                    pie_values=filtered_data['Sentiment'].value_counts().reset_index(name='count')
                    ordered_pie_values=OrderedDict()
                
                    for category in ['Positive', 'Negative', 'Neutral']:
                        ordered_pie_values[category] = pie_values.get(category,0)
                    fig=px.pie(pie_values,values='count', 
                            names='index',
                            color='index',
                            color_discrete_map={
                                            'Neutral':'#83C9FF',
                                            'Negative':'#FF2B2B',
                                            'Positive': '#0068C9'
                                            }  ,
                            hole=0.6
                            )
                    fig.update_layout(showlegend=True,height=200,margin=dict(l=1, r=1, t=1, b=1))
                    c.plotly_chart(fig,use_container_width=True)
                    idx+=1
                for c in row2:
                    c.markdown(category_list[idx])
                    filtered_data=data[(data['month_name']==select_month) & (data['Category']==category_list[idx])]
                    pie_values=filtered_data['Sentiment'].value_counts().reset_index(name='count')
                    ordered_pie_values=OrderedDict()
                
                    for category in ['Positive', 'Negative', 'Neutral']:
                        ordered_pie_values[category] = pie_values.get(category,0)
                    fig=px.pie(pie_values,values='count', 
                            names='index',
                            color='index',
                            color_discrete_map={
                                            'Neutral':'#83C9FF',
                                            'Negative':'#FF2B2B',
                                            'Positive': '#0068C9'
                                            } ,
                            hole=0.6
                            )
                    fig.update_layout(showlegend=True,height=200,margin=dict(l=1, r=1, t=1, b=1))
                    c.plotly_chart(fig,use_container_width=True)
                    idx+=1
        with st_analysis:
    # Display chart
            data['count']=1
            #domain=['Positive','Negative','Neutral']
            #range_=['#48F66D','#FB4343','#FBE143']
            color_scale = alt.Scale(
                    domain=[
                        "Positive",
                        "Negative",
                        "Neutral"        ],
                    range=["#0068C9", "#FF2B2B", "#83C9FF"] #setting custom colours for items
                )
            with st.container(border=True):
                st.markdown("<h3>Feedback Trends by Sentiment</h3>",unsafe_allow_html=True)
                bar_chart=alt.Chart(data).mark_bar().encode(
                    x=alt.X('month_name:O', axis=alt.Axis(title='Month', labels=True), scale=alt.Scale(domain=[str(m) for m in month_names]), sort=list(calendar.month_name[1:])),
                    #x=alt.X('month_name:N',sort=alt.SortField('month','ascending'),axis=alt.Axis(title="Month")),
                    y=alt.Y('sum(count)',axis=alt.Axis(title="Count of Feedback")),
                    xOffset='Sentiment',
                    color=alt.Color('Sentiment',scale=color_scale)
                    #column='sentiment:N'
                )
                st.altair_chart(bar_chart,use_container_width=True)
            with st.container(border=True):
                st.markdown("<h3>Feedback Trends</h3>",unsafe_allow_html=True)
                col1,col2=st.columns(2)        
                select_month=col1.selectbox(key="stSentiAnalysisMonth",label='Select month',options=month_names,placeholder=calendar.month_name[dt.date.today().month],index=None)
                if select_month==None:
                    select_month=calendar.month_name[dt.date.today().month]
                filtered_data=data[data['month_name']==select_month]
                pie_values=filtered_data['Sentiment'].value_counts().reset_index(name='count')
                ordered_pie_values=OrderedDict()
                
                #missing_data=[k for k in sentiment_values if k not in pie_values.keys()]
                #for miss in missing_data:
                #    pie_values[miss]=0
                for category in sentiment_values:
                    ordered_pie_values[category] = pie_values.get(category,0)
                
                fig=px.pie(pie_values,values='count', 
                        names='index',    
                        color='index',                    
                        color_discrete_map={
                                            'Neutral':'#83C9FF',
                                            'Negative':'#FF2B2B',
                                            'Positive': '#0068C9'
                                            } 
                        )
                fig.update_layout(showlegend=True,height=300,margin=dict(l=1, r=1, t=1, b=1))
                st.plotly_chart(fig,use_container_width=True)
        with dept_analysis:
            data.drop('count',axis=1)
            feedback_counts = data.groupby(['month_name', 'Department']).size().reset_index(name='count')
            total_feedback_per_month = feedback_counts.groupby('month_name')['count'].transform('sum')
            feedback_counts['percentage'] = (feedback_counts['count'] / total_feedback_per_month) * 100
            with st.container(border=True):
                st.markdown("<h3>Feedback Trends by department</h3>",unsafe_allow_html=True)
                bar_chart=alt.Chart(feedback_counts).mark_bar().encode(
                    x=alt.X('month_name:O', axis=alt.Axis(title='Month', labels=True), scale=alt.Scale(domain=[str(m) for m in month_names]), sort=list(calendar.month_name[1:])),
                    y=alt.Y('percentage:Q',axis=alt.Axis(title=r"% of Feedback")),
                    xOffset='Department',
                    color=alt.Color('Department')
                    #column='sentiment:N'
                )
                st.altair_chart(bar_chart,use_container_width=True)
            with st.container(border=True): 
                
                st.markdown("<h3>Feedback Trends</h3>",unsafe_allow_html=True)                     
                dept_list=['Electric Services','Natural Gas Services','Water Services','Energy Efficiency Programs','Renewable Energy Options','General']
                col1,col2,col3=st.columns(3)
                sel_dept=col1.selectbox(label='Select Department',options=dept_list,placeholder=dept_list[0],index=None)
                sel_senti=col3.selectbox(label='Select Feedback Sentiment',options=['Positive','Negative','Neutral'],placeholder='Positive',index=None)
                if sel_dept is None and sel_senti is None:
                    print("88here**")
                    positive_df=data[(data['Sentiment']=='Positive') & (data['Department']==dept_list[0])].groupby(['month_name','Department']).size().reset_index(name='count')
                elif sel_dept is None and sel_senti is not None:
                    positive_df=data[(data['Sentiment']==sel_senti) & (data['Department']==dept_list[0])].groupby(['month_name','Department']).size().reset_index(name='count')
                elif sel_dept is not None and sel_senti is None:
                    positive_df=data[(data['Sentiment']=='Positive') & (data['Department']==sel_dept)].groupby(['month_name','Department']).size().reset_index(name='count')
                else:
                    positive_df=data[(data['Sentiment']==sel_senti) & (data['Department']==sel_dept)].groupby(['month_name','Department']).size().reset_index(name='count')
                all_combinations = [(m, dept) for m in month_names for dept in dept_list]
                missing_data = pd.DataFrame(all_combinations, columns=['month_name', 'Department'])
                print("**here**")
                print(positive_df)
                positive_df = pd.merge(positive_df, missing_data, on=['month_name', 'Department'], how='right').fillna(0)
                line_chart=alt.Chart(positive_df).mark_line().encode(
                    x=alt.X('month_name:O', axis=alt.Axis(title='Month', labels=True), scale=alt.Scale(domain=[str(m) for m in month_names]), sort=list(calendar.month_name[1:])),
                    y=alt.Y('count',axis=alt.Axis(title='Count of feedback',labels=True)),
                    color='Department'
                )
                st.altair_chart(line_chart,use_container_width=True)
    else:
        st.markdown("No data available. Upload a file to continue.")
        st.toast("Redirecting to upload page...")
        time.sleep(3)
        st.switch_page(r"/pages/Upload.py")
if __name__=='__main__':
    
    main()
        
