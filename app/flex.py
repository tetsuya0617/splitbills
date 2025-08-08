"""
Flex message UI module with modern design
"""
from typing import List, Dict
from decimal import Decimal


def create_amount_selection_flex(
    amounts: List[Decimal], 
    app_name: str = "splitbills"
) -> Dict:
    """
    Create Flex message for amount selection with modern design
    
    Args:
        amounts: List of amount candidates
        app_name: Application name for branding
        
    Returns:
        Flex message content dictionary
    """
    
    # Create buttons for each amount
    buttons = []
    for amount in amounts[:5]:  # Max 5 buttons
        buttons.append({
            "type": "button",
            "action": {
                "type": "postback",
                "label": f"{amount:,.0f}",
                "data": f"amount={amount}",
                "displayText": f"合計金額: {amount:,.0f}"
            },
            "style": "primary",
            "height": "md",
            "margin": "sm",
            "cornerRadius": "8px"
        })
    
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": app_name,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#4A5568",
                    "align": "center"
                }
            ],
            "backgroundColor": "#F7FAFC",
            "paddingAll": "16px",
            "cornerRadius": "12px",
            "margin": "none"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "合計金額を選択",
                    "weight": "bold",
                    "size": "md",
                    "color": "#2D3748",
                    "margin": "md",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": "レシートから検出された金額候補です",
                    "size": "sm",
                    "color": "#718096",
                    "margin": "sm",
                    "wrap": True,
                    "align": "center"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#E2E8F0"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": buttons,
                    "margin": "lg",
                    "spacing": "sm",
                    "paddingAll": "8px"
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "12px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"powered by {app_name}",
                    "size": "xs",
                    "color": "#A0AEC0",
                    "align": "center"
                }
            ],
            "backgroundColor": "#F7FAFC",
            "paddingAll": "12px",
            "cornerRadius": "12px",
            "margin": "none"
        },
        "styles": {
            "header": {
                "separator": False
            },
            "footer": {
                "separator": False
            }
        }
    }


def create_error_flex(
    message: str,
    app_name: str = "splitbills"
) -> Dict:
    """
    Create error message Flex with modern design
    
    Args:
        message: Error message to display
        app_name: Application name for branding
        
    Returns:
        Flex message content dictionary
    """
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": app_name,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#4A5568",
                    "align": "center"
                }
            ],
            "backgroundColor": "#FFF5F5",
            "paddingAll": "16px",
            "cornerRadius": "12px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "エラー",
                    "weight": "bold",
                    "size": "md",
                    "color": "#E53E3E",
                    "margin": "md",
                    "align": "center"
                },
                {
                    "type": "text",
                    "text": message,
                    "size": "sm",
                    "color": "#718096",
                    "margin": "lg",
                    "wrap": True,
                    "align": "center"
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "12px"
        },
        "styles": {
            "header": {
                "separator": False
            }
        }
    }


def create_result_flex(
    total: Decimal,
    people: int,
    per_person: Decimal,
    app_name: str = "splitbills"
) -> Dict:
    """
    Create calculation result Flex message with modern design
    
    Args:
        total: Total amount
        people: Number of people
        per_person: Amount per person
        app_name: Application name for branding
        
    Returns:
        Flex message content dictionary
    """
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": app_name,
                    "weight": "bold",
                    "size": "lg",
                    "color": "#4A5568",
                    "align": "center"
                }
            ],
            "backgroundColor": "#F0FFF4",
            "paddingAll": "16px",
            "cornerRadius": "12px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "割り勘計算完了",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#22543D",
                    "align": "center",
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#E2E8F0"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "合計金額",
                            "size": "sm",
                            "color": "#718096",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": f"{total:,.0f}",
                            "size": "sm",
                            "color": "#2D3748",
                            "align": "end",
                            "weight": "bold"
                        }
                    ],
                    "margin": "lg"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "人数",
                            "size": "sm",
                            "color": "#718096",
                            "flex": 0
                        },
                        {
                            "type": "text",
                            "text": f"{people}人",
                            "size": "sm",
                            "color": "#2D3748",
                            "align": "end",
                            "weight": "bold"
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg",
                    "color": "#E2E8F0"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "一人当たり",
                            "size": "md",
                            "color": "#718096",
                            "align": "center",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": f"{per_person:,.2f}",
                            "size": "xxl",
                            "color": "#22543D",
                            "align": "center",
                            "weight": "bold",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": "#F0FFF4",
                    "cornerRadius": "8px",
                    "paddingAll": "16px",
                    "margin": "lg"
                }
            ],
            "paddingAll": "20px",
            "backgroundColor": "#FFFFFF",
            "cornerRadius": "12px"
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"powered by {app_name}",
                    "size": "xs",
                    "color": "#A0AEC0",
                    "align": "center"
                }
            ],
            "backgroundColor": "#F7FAFC",
            "paddingAll": "12px",
            "cornerRadius": "12px"
        },
        "styles": {
            "header": {
                "separator": False
            },
            "footer": {
                "separator": False
            }
        }
    }