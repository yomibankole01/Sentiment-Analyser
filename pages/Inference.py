# # Load model directly
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import streamlit as st
import streamlit.components.v1 as comp
import time
import pandas as pd
import altair as alt
from altair import datum

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
import os

api_key=os.environ['GEMINI_API_KEY']
# print(api_key)
genai.configure(api_key=api_key)

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash-8b",
  generation_config=generation_config,
                            )


tokenizer = AutoTokenizer.from_pretrained("lxyuan/distilbert-base-multilingual-cased-sentiments-student")
sentiment_classifier= AutoModelForSequenceClassification.from_pretrained("lxyuan/distilbert-base-multilingual-cased-sentiments-student")

def response_generator(session,prompt):
    response = session.send_message(prompt)
    response=response.text
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.1)
        


def sentence_generator(sentence):
    
    for word in sentence.split(" "):
        yield word + " "
        time.sleep(0.1)
    
    
def generate(prompt):
    
        encoded_prompt=tokenizer(prompt,padding='longest',add_special_tokens=True)
        
        tokenized_prompt= tokenizer(prompt, return_tensors="pt")
        outputs = sentiment_classifier(**tokenized_prompt)
        outputs=torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        sentiment_scores=outputs.detach().numpy().tolist()[0]
        
        # sentiment_scores=[0.3,0.8,0.9]
            
        return sentiment_scores
    
def filter(element):
    
    return element['sentiment_score']
    
st.header("ANALYSER",divider='green')

with st.sidebar.expander("Choose your prefered Input mode📖",expanded=True):
    st.sidebar.header('Input Mode',help='Choose the input mode',divider='red')
    option = st.sidebar.radio(label="Choose Input Mode:", options=["Single Text Analysis", "Bulk Text Analysis (CSV Upload)"])

if option == "Single Text Analysis":
    st.subheader("Enter your Text :")
    default_text = """Welcome to the sentiment analyser...Enter your text into the text area"""
    input_text = st.text_area("", value=default_text, height=200)
    
    if st.button('ANALYSE',key='start'):
        my_bar = st.progress(0, text='Analysing')
    # Create a progress bar (simulated)
        for i in range(100):
            time.sleep(0.01)
            my_bar.progress(i+1, text='Analysing ....')
    

        time.sleep(0.1)  # Small delay for animation
        my_bar.empty()

        scores=generate(prompt=input_text)
        
        
        Review_name=['Positive','Neutral','Negative']
        
        score_list=[{'sentiment_name':name,'sentiment_score':score} for name,score in zip(Review_name,scores)]
        
        score_list.sort(key=filter,reverse=True)
        
        Review_name=[score_dict['sentiment_name'] for score_dict in score_list]
        
        scores=[score_dict['sentiment_score'] for score_dict in score_list]
        
        st.subheader("Results",divider='gray')
        
        tab1,tab2=st.tabs(['ANALYSIS','SUMMARY'])
        
        with tab1:
            
            scores_data=pd.DataFrame({'Reviews':Review_name,'Sentiment Scores': scores})
        
            
            chart=alt.Chart(scores_data).mark_bar(width=100,height=60,color='green',).encode(
                                                    y=alt.Y('Reviews:N',sort=None),
                                                    x=alt.X('Sentiment Scores:Q') 
                                                    )
            
            st.altair_chart(chart, theme="streamlit", use_container_width=True)
            
        with tab2:
            
            if "messages" not in st.session_state:
                st.session_state.messages = [{"role": "model", 'content': 'Hey....I am Jarvis your personalized Sentiment Analysis Bot...\nRead the detailed analysis below.'}]
                
            history=[{"role":message['role'],"parts":[message['content'],]} for message in st.session_state.messages]
            
            message=st.write_stream(sentence_generator('Hey....I am Jarvis your personalized Sentiment Analysis Bot...\nRead the detailed analysis below.'))
            chat_session = model.start_chat(history=history)
            
            prompt=f'You are a Ai assistant built to analyse sentiments in text. You are provided with the following input text by the user and the corresponding sentiment scores in the format {Review_name}, you are to give a detailed, understandable , not too long explanation of why the scores are matched like that.\n\n Input text:\n\n{input_text}\n\nSentiment scores: {scores}'
            #st.write(prompt)
            response = st.write_stream(response_generator(session=chat_session,prompt=prompt))
            
else:
    st.subheader("Upload CSV File")
    data_file = st.file_uploader("Upload Training Data (CSV)", type=["csv"])

    if data_file is not None:
        # Read the CSV data into a Pandas DataFrame
        data = pd.read_csv(data_file)
        #st.write("Data Preview:")
        #st.write(data.head())

        # Select input and target columns
        input_col = st.selectbox("Select Input Column", data.columns)
                
        if st.button("ANALYSE"):
            
            Review_name=['Positive','Neutral','Negative']
            
            # st.success('Succesfull 🎉🎉🎉')
            
            my_bar = st.progress(0, text='Analysing')
            
            # for i in range(100):
            #     time.sleep(0.01)
            #     my_bar.progress(i+1, text='Analysing ....')
        

            # time.sleep(0.1)  # Small delay for animation
            # my_bar.empty()
            
            text_score_mapper={}
            
            for index_,text in enumerate(data[input_col].to_list()):
                
                text_score_mapper[text]=Review_name[generate(str(text)).index(max(generate(str(text))))]
                
                my_bar.progress(int((index_/(len(data[input_col].to_list())-1)*100)),text='Analysing ....')
            my_bar.empty() 
            #text_score_mapper={text:Review_name[generate(str(text)).index(max(generate(str(text))))] for text in data[input_col].to_list()}
            
            data['sentiment_class']=data[input_col].map(text_score_mapper)
            
            reviews_name=dict(data['sentiment_class'].value_counts()).keys()
            
            sentiment_scores=dict(data['sentiment_class'].value_counts()).values()
            
            tab1,tab2=st.tabs(['ANALYSIS','SUMMARY'])
        
            with tab1:
                
                scores_data=pd.DataFrame({'Reviews':reviews_name,'Sentiment Scores': sentiment_scores})
            
                
                chart=alt.Chart(scores_data).mark_bar(width=100,height=60,color='green',).encode(
                                                        y=alt.Y('Reviews:N',sort=None),
                                                        x=alt.X('Sentiment Scores:Q') 
                                                        )
                
                st.altair_chart(chart, theme="streamlit", use_container_width=True)
                
            with tab2:
                
                if "messages" not in st.session_state:
                    st.session_state.messages = [{"role": "model", 'content': 'Hey....I am Jarvis your personalized Sentiment Analysis Bot...\nRead the detailed analysis below.'}]
                    
                history=[{"role":message['role'],"parts":[message['content'],]} for message in st.session_state.messages]
                
                message=st.write_stream(sentence_generator('Hey....I am Jarvis your personalized Sentiment Analysis Bot...\nRead the detailed analysis below.'))
                chat_session = model.start_chat(history=history)
                
                prompt=f"You are a Ai assistant built to analyse sentiments in text. You are provided with the following input texts by the user from an uploaded csv file and the following sentiments were deduced {data['sentiment_class'].values}.Based on this we can infer an overal statisitcs of the number of times a particular sentiment occurs as given by {data['sentiment_class'].value_counts()}.Based on this you are to provide a detailed, understandable , not too long explanation of why the such certain sentiment type appears to be more dominant than the other. Focus you explanation on all the sentiment types.\n\nInput Text:{data[input_col].values}"
                #st.write(prompt)
                response = st.write_stream(response_generator(session=chat_session,prompt=prompt))
                
            
            
    else:
        st.error('Upload CSV file containing data to analyse')

    


            
            










