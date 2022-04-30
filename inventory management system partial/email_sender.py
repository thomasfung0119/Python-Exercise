import imaplib
from os import read 
import pdb
import smtplib  
import csv  
import traceback
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.application import MIMEApplication

class EmailBot():
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def smtp_login_email(self):
        smtpssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtpssl.ehlo()
        try:
            smtpssl.login(self.username, self.password)
            return smtpssl 
        except Exception:
            print(traceback.format_exc())
            print('Login fail')
        
    def send_email(self, receivers, subject, html, From=None, To=None, CC=None, attachment=[], csv_paths=[], image={}):
        logined_email = self.smtp_login_email()
        sender = self.username
        receivers = [receivers] if isinstance(receivers, str) else receivers
        message = MIMEMultipart()
        if From:
            message['From'] = Header(From, 'utf-8')
        if To:
            message['To'] =  "To: %s\r\n" % ",".join(receivers)
        if CC:
            message['CC'] = "CC: %s\r\n" % ", ".join(CC)
            
        message['Subject'] = Header(subject, 'utf-8')

        message.attach(MIMEText(html, 'html', 'utf-8'))



        for csvp in csv_paths:
            #pdb.set_trace()
            csvfile = MIMEText(open(str(csvp['path']), 'rb').read(), 'base64', 'utf-8')
            csvfile["Content-Disposition"] = 'attachment; filename="{}"'.format(str(csvp['path']).split('/')[-1])
            message.attach(csvfile)
             



        for atm in attachment:
            att = MIMEText(open(atm, 'rb').read(), 'base64', 'utf-8')
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = 'attachment; filename="{}"'.format(atm.split('/')[-1])
            message.attach(att)

        for img in image:
            fp = open(image[img], 'rb')
            msgImage = MIMEImage(fp.read())
            fp.close()
            msgImage.add_header('Content-ID', '<{}>'.format(img))
            message.attach(msgImage)

        result = logined_email.sendmail(sender, receivers, message.as_string())
        return result