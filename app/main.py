"""
FastAPI application for splitbills - Receipt splitting LINE bot
"""
import os
import hashlib
import hmac
import base64
import logging
from typing import Optional
from decimal import Decimal

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, PostbackEvent
)
from dotenv import load_dotenv

from app.line_client import LineClient
from app.ocr import extract_text_from_image
from app.amount import extract_amount_candidates, split_per_person
from app.session import SessionManager
from app.usage import UsageTracker
from app.flex import create_amount_selection_flex

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title=os.getenv("APP_NAME", "splitbills"))

# Initialize LINE SDK
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Initialize services
line_client = LineClient(line_bot_api)
session_manager = SessionManager()
usage_tracker = UsageTracker(
    timezone=os.getenv("PROJECT_TIMEZONE", "Asia/Tokyo"),
    monthly_cap=int(os.getenv("MONTHLY_OCR_CAP", "1000")),
    free_mode=os.getenv("FREE_MODE", "true").lower() == "true"
)


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook signature using HMAC-SHA256"""
    channel_secret = os.getenv("LINE_CHANNEL_SECRET", "").encode('utf-8')
    
    hash = hmac.new(channel_secret, body, hashlib.sha256).digest()
    signature_compare = base64.b64encode(hash).decode('utf-8')
    
    return signature == signature_compare


@app.get("/healthz")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "app": os.getenv("APP_NAME", "splitbills")}


@app.post("/callback")
async def callback(
    request: Request,
    x_line_signature: Optional[str] = Header(None, alias="X-Line-Signature")
):
    """LINE webhook callback endpoint with signature verification"""
    
    # Get request body
    body = await request.body()
    
    # Verify signature
    if not x_line_signature or not verify_signature(body, x_line_signature):
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse webhook events
    try:
        handler.handle(body.decode('utf-8'), x_line_signature)
    except InvalidSignatureError:
        logger.error("Invalid signature error from LINE SDK")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    return JSONResponse(content={"status": "ok"})


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """Handle image message for receipt OCR"""
    user_id = event.source.user_id
    reply_token = event.reply_token
    
    # Check free mode limits
    if usage_tracker.is_limit_exceeded():
        line_client.reply_text(
            reply_token,
            "Sorry, you've reached the free tier limit. It will reset next month."
        )
        return
    
    try:
        # Get image content
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = b"".join(chunk for chunk in message_content.iter_content())
        
        # Increment usage counter
        usage_tracker.increment()
        
        # Extract text from image using OCR
        ocr_text = extract_text_from_image(image_data)
        
        if not ocr_text:
            line_client.reply_text(
                reply_token,
                "Could not read the receipt text. Please take another photo."
            )
            return
        
        # Extract amount candidates
        candidates = extract_amount_candidates(ocr_text)
        
        if not candidates:
            line_client.reply_text(
                reply_token,
                "No amounts detected. Please take a clearer photo of the receipt."
            )
            return
        
        # Save session state
        session_manager.set_state(user_id, "awaiting_amount", None)
        
        # Send amount selection Flex message
        flex_message = create_amount_selection_flex(
            candidates[:5],  # Top 5 candidates
            app_name=os.getenv("APP_NAME", "splitbills")
        )
        line_client.reply_flex(reply_token, "Select amount", flex_message)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        
        if "429" in str(e) or "quota" in str(e).lower():
            message = "Vision API quota exceeded. Please try again later."
        elif "permission" in str(e).lower() or "403" in str(e):
            message = "OCR service permission error. Please contact administrator."
        else:
            message = "Error processing image. Please try again."
        
        line_client.reply_text(reply_token, message)


@handler.add(PostbackEvent)
def handle_postback(event):
    """Handle postback from Flex message buttons"""
    user_id = event.source.user_id
    reply_token = event.reply_token
    data = event.postback.data
    
    if data.startswith("amount="):
        # Parse selected amount
        try:
            amount = Decimal(data.split("=")[1])
        except:
            line_client.reply_text(reply_token, "Failed to process amount.")
            return
        
        # Update session
        session_manager.set_state(user_id, "awaiting_people", amount)
        
        # Ask for number of people
        line_client.reply_text(
            reply_token,
            f"Total: {amount:,.0f}\nHow many people to split? Enter a number."
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """Handle text message for number of people input"""
    user_id = event.source.user_id
    reply_token = event.reply_token
    text = event.message.text.strip()
    
    # Get current session state
    state = session_manager.get_state(user_id)
    
    if not state or state["stage"] != "awaiting_people":
        line_client.reply_text(
            reply_token,
            "Please send a receipt image."
        )
        return
    
    # Parse number of people
    try:
        people = int(text)
        if people <= 0:
            raise ValueError("People count must be positive")
    except:
        line_client.reply_text(
            reply_token,
            "Please enter a valid number (e.g. 3)"
        )
        return
    
    # Calculate per person amount
    total = state["selected_amount"]
    per_person = split_per_person(total, people, scale=2)
    
    # Clear session
    session_manager.clear_state(user_id)
    
    # Send result
    result_message = (
        f"【Split Bill Result】\n"
        f"Total: {total:,.0f}\n"
        f"People: {people}\n"
        f"Per person: {per_person:,.2f}"
    )
    
    line_client.reply_text(reply_token, result_message)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)