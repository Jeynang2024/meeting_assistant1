import streamlit as st
import requests
import time
from mic import record_audio
from transformers import pipeline
from textblob import TextBlob
import os


API_KEY_ASSEMBLYAI = "cb7b688c85b64d168a393d7bdd08d65c"
upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization': API_KEY_ASSEMBLYAI}


summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


def upload(filename):
    def read_file(filename, chunk_size=5242880):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data

    upload_response = requests.post(upload_endpoint, headers=headers, data=read_file(filename))
    return upload_response.json()['upload_url']


def transcribe(audio_url):
    transcript_request = {"audio_url": audio_url}
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    return transcript_response.json()['id']


def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    return requests.get(polling_endpoint, headers=headers).json()


def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = poll(transcript_id)
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']
        time.sleep(10)


def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0.2:
        return "😊 It gives Positive Vibes", sentiment
    elif sentiment < -0.2:
        return "☹️ It gives Negative Vibes", sentiment
    else:
        return "😐 It is neutral ,neither reveals negative aspects nor positive", sentiment


def summarize_text(transcription):
    summary = summarizer(transcription, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']


st.title("🎤 Audio Summarizer")
st.sidebar.write("🎶 Your Recorded Audio:")
output_file = "recorded_audio.wav"
duration = st.number_input("Enter recording duration (seconds):", min_value=5, max_value=60, value=40)
col1,col2= st.columns(2)

with col1:
    if st.button("Start recording"):
        
        st.info("Recording...")
        

        record_audio(output_file=output_file, seconds=int(duration))
        st.success("Recording complete! Audio saved as 'recorded_audio.wav'.")

  
        st.write("Uploading audio for transcription...")
        audio_url = upload(output_file)
        st.write("Audio uploaded. Transcribing...")
        if os.path.exists(output_file):
            st.sidebar.audio(output_file, format="audio/wav")
        else:
            st.sidebar.error("Audio file not found.")

        data, error = get_transcription_result_url(audio_url)
        if error:
            with col2:
                st.error(f"Error during transcription: {error}")
        else:
            transcription = data['text']
            sentiment, polarity = analyze_sentiment(transcription)
            st.sidebar.write(f"🧠 Sentiment: {sentiment}")
            with col2:
                st.write("Transcription:")
         

                st.text_area("Transcription Text", transcription,height=300)

            
                

        
                with col1:
                    st.success("Generating summary...")
                    summary = summarize_text(transcription)
                
                    st.text_area("Summary", summary)

                
                    with open("transcription.txt", "w") as f:
                        f.write(transcription)
                    with open("summary.txt", "w") as f:
                        f.write(summary)
                    st.success("Transcription and summary saved to files!")
