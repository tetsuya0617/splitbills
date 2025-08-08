"""
LINE Messaging API client helper module
"""
from typing import Dict, List, Optional
from linebot import LineBotApi
from linebot.models import (
    TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)


class LineClient:
    """Helper class for LINE Messaging API operations"""
    
    def __init__(self, line_bot_api: LineBotApi):
        """
        Initialize LINE client
        
        Args:
            line_bot_api: Configured LineBotApi instance
        """
        self.api = line_bot_api
    
    def reply_text(self, reply_token: str, text: str) -> None:
        """
        Reply with text message
        
        Args:
            reply_token: Reply token from webhook event
            text: Text message to send
        """
        self.api.reply_message(
            reply_token,
            TextSendMessage(text=text)
        )
    
    def reply_flex(self, reply_token: str, alt_text: str, contents: Dict) -> None:
        """
        Reply with Flex message
        
        Args:
            reply_token: Reply token from webhook event
            alt_text: Alternative text for notifications
            contents: Flex message contents dictionary
        """
        self.api.reply_message(
            reply_token,
            FlexSendMessage(alt_text=alt_text, contents=contents)
        )
    
    def reply_quick(
        self, 
        reply_token: str, 
        text: str,
        quick_reply_items: List[Dict[str, str]]
    ) -> None:
        """
        Reply with text message and quick reply buttons
        
        Args:
            reply_token: Reply token from webhook event
            text: Text message to send
            quick_reply_items: List of dicts with 'label' and 'text' keys
        """
        quick_reply_buttons = [
            QuickReplyButton(
                action=MessageAction(label=item["label"], text=item["text"])
            )
            for item in quick_reply_items
        ]
        
        self.api.reply_message(
            reply_token,
            TextSendMessage(
                text=text,
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        )
    
    def push_text(self, user_id: str, text: str) -> None:
        """
        Push text message to user
        
        Args:
            user_id: LINE user ID
            text: Text message to send
        """
        self.api.push_message(
            user_id,
            TextSendMessage(text=text)
        )
    
    def push_flex(self, user_id: str, alt_text: str, contents: Dict) -> None:
        """
        Push Flex message to user
        
        Args:
            user_id: LINE user ID
            alt_text: Alternative text for notifications
            contents: Flex message contents dictionary
        """
        self.api.push_message(
            user_id,
            FlexSendMessage(alt_text=alt_text, contents=contents)
        )