# -*- coding: utf-8 -*-
import requests
import json
import re
import telegram
import asyncio
import datetime
import os # Import os to access environment variables

# --- Configuration (Read from Environment Variables) ---
# Use os.getenv to read secrets passed from GitHub Actions (or set locally for testing)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Check if secrets are loaded
if not BOT_TOKEN or not CHAT_ID:
    print("Error: BOT_TOKEN or CHAT_ID environment variable not set.")
    # In a real scenario, you might want to exit or handle this differently
    # For this example, we'll let it proceed and fail during Telegram sending if None.
    # However, it's better to raise an error or exit:
    raise ValueError("BOT_TOKEN and CHAT_ID must be set as environment variables.")


# The EXACT URL provided by the user.
# Still contains dynamic tokens (tokenV2, qid, cb) and might eventually fail.
BAIDU_EXPRESS_URL = "https://alayn.baidu.com/express/appdetail/pc_express?query_from_srcid=51150&tokenV2=PB6Db7Bjgl4bhDpmXsaKgTezyeLtuZ%2Fk3dTd1GqgYg0T%2FAbVMD2LGimQ6iwBN%2B29&com=zhongtong&nu=73549140994117&qid=ceb8908d01aa384a&cb=jsonp_1743854073741_90066"

# --- Headers ---
# Mimicking browser headers MORE CLOSELY based on the initial curl command.
# IMPORTANT: The 'cookie' header is OMITTED. Using the exact cookie string
# from the example is insecure (exposes session tokens like BDUSS) and
# likely invalid anyway as cookies are session/time-bound.
# The API *might* work without the cookie, or it might fail validation.
HEADERS = {
    'Accept': '*/*', # From curl
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7', # From curl
    # 'Cookie': '...', # OMITTED - Insecure and likely invalid
    'Referer': 'https://www.baidu.com/s?wd=73549140994117&rsv_spt=1&rsv_iqid=0xac96865902bd0b9a&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&tn=68018901_16_pg&rsv_dl=tb&rsv_enter=1&rsv_sug3=2&rsv_n=2&rsv_sug2=0&rsv_btype=i&inputT=696&rsv_sug4=1024', # From curl
    'Sec-Fetch-Dest': 'script', # From curl
    'Sec-Fetch-Mode': 'no-cors', # From curl
    'Sec-Fetch-Site': 'same-site', # From curl
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15 Edg/131.0.0.0' # From curl
}

# --- Functions (parse_jsonp, send_telegram_message - kept similar) ---

def parse_jsonp(jsonp_str):
    """Parses JSONP string to extract JSON object."""
    try:
        match = re.search(r'^\s*[\w.]+\s*\((.*)\)\s*;?\s*$', jsonp_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        else:
            return json.loads(jsonp_str) # Fallback
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        print(f"Error parsing JSONP/JSON: {e}")
        print(f"Response Text (first 200 chars): {str(jsonp_str)[:200]}...")
        return None

async def send_telegram_message(bot_token, chat_id, message):
    """Sends a message to Telegram using the bot."""
    if not bot_token or not chat_id:
        print("Error: Cannot send Telegram message, BOT_TOKEN or CHAT_ID is missing.")
        return # Prevent trying to initialize bot with None token

    try:
        bot = telegram.Bot(token=bot_token)
        # Send message using MarkdownV2 for potential formatting, escape special chars
        # For simplicity, we send plain text first. Add formatting if needed later.
        await bot.send_message(chat_id=chat_id, text=message) # Consider adding parse_mode=telegram.constants.ParseMode.MARKDOWN_V2 if formatting
        print(f"Message successfully sent to Telegram chat ID {chat_id}")
    except telegram.error.TelegramError as e:
        print(f"Error sending message to Telegram: {e}")
        # Provide more context for common errors
        if "chat not found" in str(e):
            print("Hint: Check if CHAT_ID is correct and if the bot was started by the user/chat.")
        elif "Unauthorized" in str(e):
             print("Hint: Check if BOT_TOKEN is correct.")
    except Exception as e:
        print(f"An unexpected error occurred during Telegram sending: {e}")

async def query_and_send():
    """Queries express status using the specific URL and sends result to Telegram."""
    print(f"Attempting to query URL with detailed headers (excluding cookie)...")
    print(f"URL: {BAIDU_EXPRESS_URL}")

    final_message_to_send = "Default: No status update or query failed." # Default message

    try:
        response = requests.get(BAIDU_EXPRESS_URL, headers=HEADERS, timeout=30) # Increased timeout slightly
        response.raise_for_status() # Check for HTTP errors (4xx, 5xx)

        print(f"HTTP Status Code: {response.status_code}. Parsing response...")

        data = parse_jsonp(response.text)

        if data:
            if data.get('status') == 0 and 'data' in data and 'context' in data['data'] and data['data']['context']:
                latest_update = data['data']['context'][0] # Assuming newest is first
                timestamp = latest_update.get('time')
                description = latest_update.get('desc', 'No description available.')

                time_str = "Timestamp N/A"
                if isinstance(timestamp, (int, float)):
                    try:
                        # Assuming timestamp is in seconds UTC
                        dt_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                        # Convert to a specific timezone if needed, e.g., Asia/Bangkok (ICT, UTC+7)
                        # For simplicity, keeping UTC or server's local time interpretation for now.
                        # Let's format clearly with timezone info if possible
                        # dt_object_local = dt_object.astimezone() # Convert to system's local timezone
                        # time_str = dt_object_local.strftime("%Y-%m-%d %H:%M:%S %Z")
                        time_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") # Simpler local time

                    except Exception as time_e:
                        print(f"Timestamp conversion error: {time_e}")
                        time_str = f"Raw timestamp: {timestamp}"

                tracking_number = "73549140994117" # Hardcoded
                company_name = data.get('data', {}).get('officalService', {}).get('comName', '中通快递')

                final_message_to_send = (
                    f"✅ 快递更新 ({company_name} - {tracking_number}):\n"
                    f"⏰ 时间: {time_str}\n"
                    f"📄 状态: {description}"
                )
                print(f"Successfully extracted status: {description}")

            else:
                error_msg = data.get('msg', 'No error message from API.')
                status_code = data.get('status', 'N/A')
                error_code = data.get('error_code', 'N/A')
                final_message_to_send = f"⚠️ 查询失败 (API Response):\n状态码: {status_code}\n错误码: {error_code}\n消息: {error_msg}"
                print(f"API indicated failure: Status={status_code}, Msg={error_msg}")
        else:
            final_message_to_send = "❌ 查询失败: 无法解析服务器响应 (JSONP/JSON Error)."
            print("Failed to parse API response.")

    except requests.exceptions.Timeout:
        error_msg = "❌ 查询失败: 请求百度 API 超时."
        print(error_msg)
        final_message_to_send = error_msg
    except requests.exceptions.HTTPError as e:
        error_msg = f"❌ 查询失败: HTTP Error {e.response.status_code}.\nResponse: {e.response.text[:200]}..."
        print(error_msg)
        final_message_to_send = error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ 查询失败: 网络请求错误: {e}"
        print(error_msg)
        final_message_to_send = error_msg
    except Exception as e:
        # Catch other potential errors, e.g., during Telegram init if token is bad
        error_msg = f"❌ 发生意外错误: {e}"
        print(error_msg)
        final_message_to_send = error_msg

    # --- Send to Telegram ---
    print("\nSending result to Telegram...")
    await send_telegram_message(BOT_TOKEN, CHAT_ID, final_message_to_send)

# --- Run the main asynchronous function ---
if __name__ == "__main__":
    print("Executing Express Check Script...")
    # Check for tokens at the start in __main__ as well
    if not BOT_TOKEN or not CHAT_ID:
        print("Critical Error: BOT_TOKEN or CHAT_ID environment variables are not set. Exiting.")
    else:
        asyncio.run(query_and_send())
    print("Script finished.")
