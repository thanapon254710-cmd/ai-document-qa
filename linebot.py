from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, FileMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from utils import process_pdf, create_qa_chain
import os, requests
from dotenv import load_dotenv
from io import BytesIO

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))

# เก็บ qa_chain ของแต่ละ user
user_chains = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=FileMessageContent)
def handle_file(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        # ดาวน์โหลดไฟล์จาก Line
        message_id = event.message.id
        headers = {"Authorization": f"Bearer {os.getenv('CHANNEL_ACCESS_TOKEN')}"}
        res = requests.get(f"https://api-data.line.me/v2/bot/message/{message_id}/content", headers=headers)
        
        # Process PDF
        pdf_file = BytesIO(res.content)
        pdf_file.name = "file.pdf"
        chunks = process_pdf(pdf_file)
        user_chains[event.source.user_id] = create_qa_chain(chunks)
        
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="✅ อัปโหลด PDF สำเร็จ! ถามคำถามได้เลยครับ")]
        ))

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_id = event.source.user_id
    question = event.message.text
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        if user_id not in user_chains:
            reply = "กรุณาส่งไฟล์ PDF ก่อนนะครับ 📄"
        else:
            reply = user_chains[user_id](question)
        
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        ))

if __name__ == "__main__":
    app.run(port=5000)