import json
import base64
import io
import os
import wave
from flask import Flask, render_template, send_file, request
import numpy as np


app = Flask(__name__)

def parse_log_file(file_path):
    logs = []
    current_input_audio = None
    current_response_audio = None
    current_audio_transcript = None
    audio_counter = 0

    with open(file_path, 'r') as f:
        for line in f:
            log_entry = json.loads(line)

            if log_entry['data']['type'] == 'input_audio_buffer.append':
                if current_input_audio is None:
                    current_input_audio = log_entry
                else:
                    current_input_audio['data']['audio'] += log_entry['data']['audio']
                continue

            if log_entry['data']['type'] == 'response.audio_transcript.delta':
                if current_audio_transcript is None:
                    current_audio_transcript = log_entry
                else:
                    current_audio_transcript['data']['delta'] += log_entry['data']['delta']
                continue
            
            if log_entry['data']['type'] == 'response.audio.delta':
                if current_response_audio is None:
                    current_response_audio = log_entry
                else:
                    current_response_audio['data']['delta'] += log_entry['data']['delta']
                continue
            
            if log_entry['data']['type'] == 'response.done':
                if current_input_audio:
                    logs.append(deal_audio_log(current_input_audio, audio_counter))
                    audio_counter += 1
                    current_input_audio = None
                if current_audio_transcript:
                    logs.append(current_audio_transcript)
                    current_audio_transcript = None
                if current_response_audio:
                    logs.append(deal_audio_log(current_response_audio, audio_counter, "delta"))
                    audio_counter += 1
                    current_response_audio = None
            logs.append(log_entry)

    if current_input_audio:
        logs.append(deal_audio_log(current_input_audio, audio_counter))
    if current_response_audio:
        logs.append(deal_audio_log(current_response_audio, audio_counter, "delta"))
    if current_audio_transcript:
        logs.append(current_audio_transcript)

    logs = sorted(logs, key=lambda x: x['timestamp'])
    return logs

def deal_audio_log(log_entry, audio_counter, key="audio"):
    audio_data = base64.b64decode(log_entry['data'][key])
    audio_filename = f'audio_{audio_counter}.wav'
    save_audio(audio_data, os.path.join('static', audio_filename))
    log_entry['audio_file'] = audio_filename
    return log_entry

def save_audio(audio_data, filename):
    # Convert raw PCM data to numpy array
    audio_np = np.frombuffer(audio_data, dtype=np.int16)

    # Create WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(24000)  # 24kHz
        wav_file.writeframes(audio_np.tobytes())

@app.route('/', methods=['GET', 'POST'])
def index():
    logs = []
    if request.method == 'POST':
        log_path = request.form['log_path']
        if os.path.exists(log_path):
            logs = parse_log_file(log_path)
        else:
            return "Log file not found", 400
    return render_template('index.html', logs=logs)


@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(f"static/{filename}", mimetype="audio/wav")

if __name__ == '__main__':
    app.run(debug=True)
