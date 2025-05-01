import pyaudio
import numpy as np
import requests
import tkinter as tk
import wave
import threading
import time
import io
from PIL import Image, ImageTk

# API key and host
API_KEY = '9d16879208mshc94a76428d56db0p146463jsndf045f60e05a'
API_HOST = 'shazam.p.rapidapi.com'

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 30  # Increased recording time to 30 seconds
AUDIO_FILE = "assets/sample.wav"

# Audio stream
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

## CONVERTING THE AUDIO TO DB ##
def get_decibel(data):
    rms = np.sqrt(np.mean(np.square(data)))
    db = 20 * np.log10(rms + 1e-6)
    return round(db, 2)

## RECORDING DA AUDIO ##
def record_sample():
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    with wave.open(AUDIO_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return AUDIO_FILE

## IDENTIFY THE SONG WIT DA API##
def identify_song():
    record_sample()  # Record the audio sample
    with open(AUDIO_FILE, 'rb') as f:
        payload = f.read()  # Read the audio data as binary

    url = "https://shazam.p.rapidapi.com/songs/detect"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": API_HOST,
        "Content-Type": "application/octet-stream",  # Binary data for the audio
    }

    result_label.config(text="Identifying...")
    cover_label.config(image='')  # Clear the previous album cover

    try:
        response = requests.post(url, headers=headers, data=payload)  # Send the audio data as binary
        response.raise_for_status()  # Will raise an error for non-2xx responses
        data = response.json()

        if 'track' in data:
            song = data['track']['title']
            artist = data['track']['subtitle']
            result_label.config(text=f"{song} by {artist}")

            # Fetch album cover
            img_url = data['track']['images']['coverart']
            img_response = requests.get(img_url)
            img_data = Image.open(io.BytesIO(img_response.content))
            img_data = img_data.resize((120, 120), Image.ANTIALIAS)
            img_tk = ImageTk.PhotoImage(img_data)
            cover_label.config(image=img_tk)
            cover_label.image = img_tk
        else:
            result_label.config(text="No match found.")
    
    except requests.exceptions.RequestException as e:
        result_label.config(text="Error communicating with Shazam.")
        print(f"Request error: {e}")
    except Exception as e:
        result_label.config(text="No match found.")
        print(f"An error occurred: {e}")

## FOR DA DECIBELS TO UPDATE IN REAL TIME ##
def update_decibel():
    while True:
        try:
            data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
            db = get_decibel(data)
            db_label.config(text=f"Level: {db} dB")
            time.sleep(0.5)
        except:
            pass

## FOR DA USER INTERFACE ##
root = tk.Tk()
root.title("SSHL - Smart Sound & Hearing Lab")
root.geometry("340x360")

tk.Label(root, text="SSHL", font=("Helvetica", 18, "bold")).pack(pady=5)
db_label = tk.Label(root, text="Level: -- dB", font=("Helvetica", 14))
db_label.pack(pady=10)

identify_button = tk.Button(
    root,
    text="Scan Sound",
    font=("Helvetica", 12),
    command=lambda: threading.Thread(target=identify_song).start()
)
identify_button.pack(pady=10)

result_label = tk.Label(root, font=("Helvetica", 12))
result_label.pack(pady=5)

cover_label = tk.Label(root)
cover_label.pack(pady=10)

threading.Thread(target=update_decibel, daemon=True).start()
root.mainloop()
