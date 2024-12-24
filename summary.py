import streamlit as st
import requests
import time
from mic import record_audio
from transformers import pipeline
from textblob import TextBlob

# Constants
API_KEY_ASSEMBLYAI = "cb7b688c85b64d168a393d7bdd08d65c"
upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization': API_KEY_ASSEMBLYAI}

# Load the summarizer pipeline
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Upload file to AssemblyAI
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

# Transcribe audio
def transcribe(audio_url):
    transcript_request = {"audio_url": audio_url}
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    return transcript_response.json()['id']

# Polling for transcription completion
def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    return requests.get(polling_endpoint, headers=headers).json()

# Get transcription result
def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while True:
        data = poll(transcript_id)
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']
        time.sleep(10)

# Sentiment Analysis
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0:
        return "Positive", sentiment
    elif sentiment < 0:
        return "Negative", sentiment
    else:
        return "Neutral", sentiment

# Summarize transcription
def summarize_text(transcription):
    summary = summarizer(transcription, max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

# Streamlit App
st.title("Audio Summarizer and Sentiment Analysis")
output_file = "recorded_audio.wav"
duration = st.number_input("Enter recording duration (seconds):", min_value=5, max_value=60, value=40)

# Record audio
if st.button("Start recording"):
    
    st.info("Recording...")
    

    record_audio(output_file=output_file, seconds=int(duration))
    st.success("Recording complete! Audio saved as 'recorded_audio.wav'.")

   # Upload and process
    st.write("Uploading audio for transcription...")
    audio_url = upload(output_file)
    st.write("Audio uploaded. Transcribing...")

    data, error = get_transcription_result_url(audio_url)
    if error:
        st.error(f"Error during transcription: {error}")
    else:
        transcription = data['text']
        st.write("Transcription:")
        st.text_area("Transcription Text", transcription)

        # Sentiment Analysis
        sentiment, polarity = analyze_sentiment(transcription)
        st.write(f"Sentiment: {sentiment} (Polarity: {polarity})")

        # Summarization
        st.write("Generating summary...")
        summary = summarize_text(transcription)
        st.text_area("Summary", summary)

        # Save transcription and summary
        with open("transcription.txt", "w") as f:
            f.write(transcription)
        with open("summary.txt", "w") as f:
            f.write(summary)
        st.success("Transcription and summary saved to files!")
