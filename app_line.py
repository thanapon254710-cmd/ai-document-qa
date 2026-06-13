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

# store each user's chain in memory
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

# store chunks for each user as a list
user_chunks = {}

@handler.add(MessageEvent, message=FileMessageContent)
def handle_file(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        user_id = event.source.user_id
        
        message_id = event.message.id
        headers = {"Authorization": f"Bearer {os.getenv('CHANNEL_ACCESS_TOKEN')}"}
        res = requests.get(f"https://api-data.line.me/v2/bot/message/{message_id}/content", headers=headers)
        
        pdf_file = BytesIO(res.content)
        pdf_file.name = "file.pdf"
        new_chunks = process_pdf(pdf_file)
        
        if user_id not in user_chunks:
            user_chunks[user_id] = []
        user_chunks[user_id].extend(new_chunks)
        
        # create new chain with all chunks
        user_chains[user_id] = create_qa_chain(user_chunks[user_id])
        
        count = len(user_chunks[user_id])
        line_bot_api.reply_message(ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=f"✅ อัปโหลดสำเร็จ! ตอนนี้มี {count} chunks จากทุกไฟล์ที่ส่งมา ถามได้เลยครับ")]
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)