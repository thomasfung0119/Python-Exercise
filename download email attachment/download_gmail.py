import logging
import os
import getpass
from imbox import Imbox # pip install imbox
import traceback
import zipfile

# enable less secure apps on your google account
# https://myaccount.google.com/lesssecureapps

searching_file = "attachment.zip"
host = "imap.gmail.com"
username = "youremail@gmail.com"
password = getpass.getpass('Password: ')
download_folder = f"saving folder"

def download_gmail_main():
  if not os.path.isdir(download_folder):
      os.makedirs(download_folder, exist_ok=True)
      
  mail = Imbox(host, username=username, password=password, ssl=True, ssl_context=None, starttls=False)
  messages = mail.messages() # defaults to inbox
  for (uid, message) in messages:
      for idx, attachment in enumerate(message.attachments):
          try:
              att_fn = attachment.get('filename')
              if (att_fn==searching_file):
                download_path = f"{download_folder}/{att_fn}"
                with open(download_path, "wb") as fp:
                  fp.write(attachment.get('content').read()) 
          except:
              print(traceback.print_exc())

  mail.logout()
  with zipfile.ZipFile(download_folder+'/'+searching_file,"r") as zip_ref:
    zip_ref.extractall(download_folder)
  if os.path.exists(download_folder+'/'+searching_file):
    os.remove(download_folder+'/'+searching_file)
  else:
    print("The file does not exist")

def main():
  download_gmail_main()

if __name__ == "__main__":
    main()
