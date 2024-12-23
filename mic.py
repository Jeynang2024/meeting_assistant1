import pyaudio
print("pyaudio ")
import wave



def record_audio(output_file="output.wav", Rate=48000,Format=pyaudio.paInt16,Channel=1,Frames_per_buffer=3200,seconds=60):
    p=pyaudio.PyAudio()
    stream=p.open(
        format=Format,
        channels=Channel,
        rate=Rate,
        input=True,
        frames_per_buffer=Frames_per_buffer
    )
    print("start recording")
    
    frames=[]
    for i in range(0,int(Rate/Frames_per_buffer*seconds)):
        data=stream.read(Frames_per_buffer)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(Channel)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(Rate)
        wf.writeframes(b''.join(frames))

    print(f"Recording saved to {output_file}")
