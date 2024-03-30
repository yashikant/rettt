from flask import Flask, request, jsonify, send_file
import os
import socket
from threading import Thread
from queue import Queue
import pyttsx3
import logging

app = Flask(__name__)
engine = pyttsx3.init()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize a queue and a worker thread for pyttsx3
speech_queue = Queue()

def pyttsx3_worker():
    while True:
        text_to_speak = speech_queue.get()
        if text_to_speak is None:
            break  # Allows the thread to be stopped
        try:
            engine.say(text_to_speak)
            engine.runAndWait()
        except Exception as e:
            logging.error(f"Error in pyttsx3_worker: {e}")
        finally:
            speech_queue.task_done()

# Start the worker thread
tts_thread = Thread(target=pyttsx3_worker)
tts_thread.start()

# Function to check internet connection
def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except OSError:
        return False

# Function to execute commands
def execute_command(command):
    online_commands = {
        "open google": "start https://www.google.com",
        "check the weather": "start https://www.google.com/search?q=weather",
        "read the news": "start https://indianexpress.com",
        "play on youtube": "start https://www.youtube.com",
        "what's trending on twitter?": "start https://twitter.com/explore/trending",
        "navigate to": "Starting navigation to the specified location..."
        # Define your online commands here
    }

    offline_commands = {
        "open notepad": "start notepad.exe",
        "check battery status": "powercfg /batteryreport",
        "tell me the date": "echo %date%",
        "what time is it?": "echo %time%",
        "set an alarm for": "Scheduling alarms is not supported via command line",
        "create a reminder": "Reminders are not supported via command line",
        "play music": "start wmplayer",  # This will open Windows Media Player
        "stop music": "taskkill /IM wmplayer.exe",  # This will close Windows Media Player
        "volume up": "nircmd.exe changesysvolume 2000",  # Requires NirCmd utility
        "volume down": "nircmd.exe changesysvolume -2000",  # Requires NirCmd utility
        "open calculator": "start calc.exe"
        # Define your offline commands here
    }

    try:
        for cmd, action in offline_commands.items():
            if cmd in command:
                logging.info(f"Executing offline command: {action}")
                os.system(action)
                return f"Executing offline command: {cmd}"

        if check_internet_connection():
            for cmd, action in online_commands.items():
                if cmd in command:
                    logging.info(f"Executing online command: {action}")
                    os.system(action)
                    return f"Executing online command: {cmd}"
        else:
            return "No internet connection or command not recognized."
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return "Error executing command."

    return "Command not recognized."

@app.route('/process-command', methods=['POST'])
def process_command():
    data = request.json
    command = data['command'].lower()
    response = execute_command(command)
    
    # Add the response to the queue instead of calling runAndWait directly
    speech_queue.put(response)
    
    return jsonify({'message': response})

@app.route('/')
def index():
    return send_file('index.html')

# Stop the worker thread when the application exits
@app.teardown_appcontext
def stop_tts_thread(exception=None):
    speech_queue.put(None)
    tts_thread.join()

if __name__ == '__main__':
    app.run(debug=True)
