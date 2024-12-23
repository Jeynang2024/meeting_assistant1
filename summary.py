import requests
import sys
import time
import torch
import transformers
from textblob import TextBlob
from transformers import pipeline
from mic import record_audio



#recording of audio file

output_file = "recorder_audio.wav"
duration = 20
record_audio(output_file = output_file, seconds=duration)
print("audio recording complete !! . Proceeding further...")



#using api of assmbly ai

API_KEY_ASSEMBLYAI = "cb7b688c85b64d168a393d7bdd08d65c"
upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
headers = {'authorization':API_KEY_ASSEMBLYAI}

filename = output_file

#uploading file

def upload(filename):
    def read_file(filename , chunk_size=5242880):
        with open(filename,'rb') as _file:
            while True:
                data = _file.read(chunk_size)
                if not data:
                    break
                yield data


    upload_response = requests.post(upload_endpoint,headers=headers,data=read_file(filename))
    

    audio_url = upload_response.json()['upload_url']
    return audio_url

#transcribe

def transcribe(audio_url):
    transcript_request = {"audio_url" : audio_url}
    transcript_response = requests.post(transcript_endpoint,json = transcript_request, headers=headers)
    
    job_id=transcript_response.json()['id']
    return job_id





#poll

def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response=requests.get(polling_endpoint, headers =headers)
    return polling_response.json()

def get_transcription_result_url(audio_url):
    transcript_id = transcribe(audio_url)
    while(True):
        data = poll(transcript_id)
        
        if data['status'] == 'completed':
            return data,None
        elif data['status'] == 'error':
            return data, data['error']
        print("waiting 30 seconds...")
        time.sleep(30)


summarizer = pipeline("summarization" , model ="sshleifer/distilbart-cnn-12-6")



#summary of the text

def summarize_text(transcription):
    summary = summarizer(transcription , max_length = 150 , min_length= 30, do_sample = False)
    return summary[0]['summary_text']





#save transcription into text file

def save_transcript(audio_url):
    data , error = get_transcription_result_url(audio_url)   

    if data:
        text_filename = filename + ".txt"
        with open(text_filename, "w") as f:
            f.write(data['text'])
        print("transcription saved !!")

        sentiment = analyze_sentiment(data['text'])
        print(f"sentiment analysis result : {sentiment}")

        summary = summarize_text(data['text'])
        print("summary :")
        print(summary)

        summary_filename = filename + "_summary.txt"
        with open(summary_filename , "w") as f:
            f.write(summary)
        print(f"summary saved to {summary_filename} !!")

    
    
    
    elif error :
        print("Error!!" , error)




#sentiment analysis

def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity

    if sentiment > 0:
        return "positive", sentiment
    elif sentiment < 0:
        return "negative" , sentiment
    else:
        return "neutral",sentiment

audio_url = upload(filename)
save_transcript(audio_url)