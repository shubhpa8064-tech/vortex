
import asyncio
import os
import subprocess
import webbrowser
import tempfile
import time
import json
import random
import requests
import speech_recognition as sr
import pygame
from openai import OpenAI
import edge_tts
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import re
from yt_dlp import YoutubeDL

# ======================= CONFIG =======================
OPENROUTER_API_KEY = "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"  # <-- OpenRouter Key
OPENWEATHER_API_KEY = ""  # <-- OpenWeatherMap Key
AI_NAME = "Vortex"
VOICE_NAME = "en-US-ChristopherNeural"
REMINDER_FILE = "reminders.json"

pygame.mixer.init()

# ====================== Vortex Class ======================
class VortexAI:
    def __init__(self):
        self.ai_name = AI_NAME
        self.memory = []  # store last 5 messages for AI context
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"🔥 {self.ai_name} SYSTEM ONLINE | ULTIMATE MODE")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": f"{self.ai_name} AI Assistant",
                }
            )
            print(f"✅ OpenRouter Brain Linked, Sir.")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    # ------------------- SPEAK -------------------
    async def _speak_async(self, text):
        if not text: return
        temp_file = os.path.join(tempfile.gettempdir(), f"vortex_{int(time.time())}.mp3")
        try:
            communicate = edge_tts.Communicate(text, VOICE_NAME)
            await communicate.save(temp_file)
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            try: os.remove(temp_file)
            except: pass
        except: pass

    def speak(self, text):
        clean_text = text.replace('*', '').replace('#', '').strip()
        print(f"🤖 {self.ai_name}: {clean_text}")
        try:
            asyncio.run(self._speak_async(clean_text))
        except:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._speak_async(clean_text))

    # ------------------- LISTEN -------------------
    def listen(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"🎤 Listening...")
            r.adjust_for_ambient_noise(source, duration=0.8)
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
                command = r.recognize_google(audio, language='en-in')
                print(f"👤 You: {command}")
                return command.lower()
            except:
                return None

    # ------------------- VOLUME CONTROL -------------------
    def get_volume_control(self):
        devices = AudioUtilities.GetSpeakers()
        default_speaker = devices[0]
        interface = default_speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        return volume

    # ------------------- REMINDERS -------------------
    def load_reminders(self):
        if os.path.exists(REMINDER_FILE):
            with open(REMINDER_FILE, "r") as f:
                return json.load(f)
        return []

    def save_reminders(self, reminders):
        with open(REMINDER_FILE, "w") as f:
            json.dump(reminders, f, indent=2)

    def add_reminder(self, text):
        reminders = self.load_reminders()
        reminders.append(text)
        self.save_reminders(reminders)
        self.speak(f"Reminder added: {text}, Sir.")

    def list_reminders(self):
        reminders = self.load_reminders()
        if reminders:
            self.speak("Here are your reminders, Sir: " + "; ".join(reminders))
        else:
            self.speak("No reminders found, Sir.")

    # ------------------- FUN -------------------
    def tell_joke(self):
        jokes = [
            "Why did the programmer go broke? Because he used up all his cache!",
            "Why do Java developers wear glasses? Because they don't see sharp.",
            "I told my computer I needed a break, and it said no problem — it would go to sleep."
        ]
        self.speak(random.choice(jokes))

    def motivational_quote(self):
        quotes = [
            "Push yourself, because no one else is going to do it for you.",
            "Success is not final, failure is not fatal: It is the courage to continue that counts.",
            "Dream big and dare to fail."
        ]
        self.speak(random.choice(quotes))

    def trivia_fact(self):
        facts = [
            "Did you know? Honey never spoils.",
            "Did you know? Octopuses have three hearts.",
            "Did you know? Bananas are berries but strawberries are not."
        ]
        self.speak(random.choice(facts))

    # ------------------- WEATHER -------------------
    def weather_info(self, city="Lucknow"):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
            res = requests.get(url).json()
            desc = res["weather"][0]["description"]
            temp = res["main"]["temp"]
            self.speak(f"The weather in {city} is {desc} with {temp} degrees Celsius, Sir.")
        except:
            self.speak("Unable to get weather information, Sir.")

    # ------------------- YOUTUBE DIRECT PLAY -------------------
    def play_on_youtube(self, query):
        try:
            with YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                webbrowser.open(info['webpage_url'])
        except:
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

    # ------------------- SYSTEM COMMANDS -------------------
    def advanced_system_commands(self, command):
        command = command.lower()

        # Volume
        try:
            volume = self.get_volume_control()
            if "volume up" in command:
                volume.StepUp(); self.speak("Volume increased, Sir."); return True
            if "volume down" in command:
                volume.StepDown(); self.speak("Volume decreased, Sir."); return True
            if "mute" in command:
                volume.SetMute(1, None); self.speak("Volume muted, Sir."); return True
            if "unmute" in command:
                volume.SetMute(0, None); self.speak("Volume unmuted, Sir."); return True
        except: pass

        # Brightness
        if "brightness" in command:
            match = re.search(r"(?:set\s+)?brightness\s*(?:to)?\s*(\d+)", command)
            if match:
                value = int(match.group(1))
                try:
                    sbc.set_brightness(max(0, min(value, 100)))
                    self.speak(f"Brightness set to {value}%, Sir."); return True
                except:
                    self.speak("Unable to set brightness on this device, Sir."); return True

        # Open apps
        if "open notepad" in command:
            subprocess.Popen("notepad.exe"); self.speak("Notepad opened, Sir."); return True
        if "open vscode" in command:
            subprocess.Popen(r"C:\Users\Shubh Patel\AppData\Local\Programs\Microsoft VS Code\Code.exe")
            self.speak("VSCode opened, Sir."); return True
        if "open calculator" in command:
            subprocess.Popen("calc.exe"); self.speak("Calculator opened, Sir."); return True

        # Shutdown / Restart / Lock
        if "shutdown" in command:
            self.speak("Shutting down, Sir."); os.system("shutdown /s /t 5"); return True
        if "restart" in command:
            self.speak("Restarting, Sir."); os.system("shutdown /r /t 5"); return True
        if "lock" in command:
            self.speak("Locking system, Sir."); os.system("rundll32.exe user32.dll,LockWorkStation"); return True

        return False

    # ------------------- PROCESS COMMAND -------------------
    def process_command(self, command):
        if not command: return

        # First: system commands
        if self.advanced_system_commands(command):
            return

        # --- Reminders ---
        if "add reminder" in command:
            text = command.replace("add reminder", "").strip()
            self.add_reminder(text); return
        if "show reminders" in command:
            self.list_reminders(); return

        # --- Fun ---
        if "joke" in command:
            self.tell_joke(); return
        if "quote" in command:
            self.motivational_quote(); return
        if "trivia" in command:
            self.trivia_fact(); return

        # --- Weather ---
        if "weather" in command:
            city_match = re.search(r"weather in (\w+)", command)
            city = city_match.group(1) if city_match else "Lucknow"
            self.weather_info(city); return

        # --- Offline commands ---
        if "open youtube" in command:
            self.speak("Opening YouTube, Sir."); webbrowser.open("https://www.youtube.com"); return

        if "chrome" in command:
            if "close" in command:
                self.speak("Closing Chrome, Sir."); os.system("taskkill /f /im chrome.exe")
            else:
                self.speak("Launching Chrome, Sir."); subprocess.Popen(["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"])
            return

        # --- PLAY ON YOUTUBE DIRECTLY ---
        if "play" in command:
            query = command.replace("play", "").strip()
            self.speak(f"Playing {query} on YouTube, Sir.")
            self.play_on_youtube(query)
            return

        # --- AI responses ---
        try:
            self.memory.append({"role": "user", "content": command})
            self.memory = self.memory[-5:]  # last 5 messages
            response = self.client.chat.completions.create(
                model="openrouter/free",
                messages=[{"role": "system", "content": f"You are a friendly AI named {self.ai_name}. End every reply with 'Sir'."}] + self.memory
            )
            ai_reply = response.choices[0].message.content
            self.memory.append({"role": "assistant", "content": ai_reply})
            self.speak(ai_reply)
        except:
            self.speak("Sir, I'm having trouble connecting to OpenRouter, Sir.")

# ====================== MAIN ======================
if __name__ == "__main__":
    bot = VortexAI()
    print("\n[1] Voice | [2] Text")
    choice = input("Mode: ").strip()
    bot.speak("System ready. Ultimate modules loaded, Sir.")

    while True:
        cmd = bot.listen() if choice == "1" else input("\n👤 You: ").strip()
        if cmd:
            if any(x in cmd for x in ["exit", "stop", "bye"]):
                bot.speak("Powering down. See you soon, Sir!")
                break
            bot.process_command(cmd)
