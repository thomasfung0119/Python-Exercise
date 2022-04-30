from slack_sdk import WebClient
import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
SLACK_BOT_TOKEN_TEST="xoxb-your bot token-000000000000000000000000000000000000"
SLACK_BOT_TOKEN_PROD="xoxb-your bot token-000000000000000000000000000000000000"
bot = WebClient(token=SLACK_BOT_TOKEN_TEST)

upload_file_path = "file path"
upload_channel = "#general"
upload_message = "message"

def printmessage(upchannel, message):
  try:
    bot.chat_postMessage(
      channel=upchannel,
      text= message
    )
  except :
    # You will get a SlackApiError if "ok" is False
    print("message error")  # str like 'invalid_auth', 'channel_not_found'

def printfile(upchannel, filepath):
  try:
    bot.files_upload(
      channels=upchannel,
      as_user=True, 
      filename=filepath, 
      file=open(filepath, 'rb'),
    )
  except :
    # You will get a SlackApiError if "ok" is False
    print("file error")  # str like 'invalid_auth', 'channel_not_found'

def main():
  printmessage(upload_channel, upload_message)
  printfile(upload_channel, upload_file_path)

if __name__ == "__main__":
  main()