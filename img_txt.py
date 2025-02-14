import requests
import time
import pytesseract
from PIL import Image
import os
import json

# Token bot Telegram dan URL API
BOT_TOKEN = "7836089937:AAFvfIzrMQjo27RjcOpm1A3dYBY9LIm5Kk4"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
HISTORY_FILE = "history.txt"
OFFSET = 0

def get_updates():
    """Mendapatkan update terbaru dari bot."""
    response = requests.get(f"{API_URL}/getUpdates", params={"offset": OFFSET})
    return response.json()

def send_message(chat_id, message):
    """Mengirim pesan ke pengguna."""
    requests.post(f"{API_URL}/sendMessage", data={"chat_id": chat_id, "text": message})

def download_image(file_id):
    """Mengunduh gambar dari Telegram."""
    file_info = requests.get(f"{API_URL}/getFile", params={"file_id": file_id}).json()
    file_path = file_info.get("result", {}).get("file_path")

    if file_path:
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        image_path = "/tmp/telegram_image.jpg"
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)
            return image_path
    return None

def improve_image_quality(image_path):
    """Meningkatkan kualitas gambar sebelum OCR."""
    img = Image.open(image_path)
    img = img.convert("L").resize((img.width * 2, img.height * 2))
    improved_path = "/tmp/improved_image.jpg"
    img.save(improved_path)
    return improved_path

def convert_image_to_text(image_path):
    """Mengonversi gambar menjadi teks menggunakan Tesseract."""
    return pytesseract.image_to_string(Image.open(image_path), lang="ind").strip()

def save_to_history(chat_id, image_text):
    """Menyimpan hasil OCR ke file history.txt."""
    with open(HISTORY_FILE, "a") as f:
        f.write(f"Chat ID: {chat_id}\n{image_text}\n{'-'*26}\n")

def process_message(chat_id, file_id):
    """Memproses gambar dari pengguna dan mengirim hasil OCR."""
    send_message(chat_id, "Ditunggu ya, pesan sedang diproses...🙏")

    image_path = download_image(file_id)
    if image_path:
        improved_image = improve_image_quality(image_path)
        image_text = convert_image_to_text(improved_image)

        if image_text:
            send_message(chat_id, image_text)
            save_to_history(chat_id, image_text)
        else:
            send_message(chat_id, "Maaf, tidak ada teks yang bisa dibaca dari gambar.")
    else:
        send_message(chat_id, "Gagal mengunduh gambar. Tolong coba lagi.")

def process_updates(updates):
    """Memproses update dari bot."""
    global OFFSET

    for update in updates.get("result", []):
        chat_id = update.get("message", {}).get("chat", {}).get("id")
        photo = update.get("message", {}).get("photo", [])
        file_id = photo[-1]["file_id"] if photo else None

        if file_id:
            process_message(chat_id, file_id)
        else:
            send_message(chat_id, "Tolong kirimkan gambar untuk diubah menjadi teks.")

        OFFSET = update["update_id"] + 1

def bot_standby():
    """Menjalankan bot dalam mode standby."""
    while True:
        updates = get_updates()
        if updates.get("result"):
            process_updates(updates)
        time.sleep(2)

if __name__ == "__main__":
    bot_standby()
