#!/usr/bin/env python
# coding: utf-8

#
# import needed modules.
# pyzabbix is needed, see https://github.com/lukecyca/pyzabbix
#
# Pillow is also needed, see https://github.com/python-pillow/Pillow
#
#
import argparse
import ConfigParser
import os
import os.path
import distutils.util
import requests
import time
import sys
from cStringIO import StringIO
from PIL import Image
from pyzabbix import ZabbixAPI
import cStringIO

username = "root"
password = "zabbix123"
graphid = 14931
api = "http://localhost"
period=9600

def getGraph(graphid, username, password, api, period):
    zapi = ZabbixAPI(url='http://localhost', user='root', password='zabbix123')
    zapi.session.verify = False

    # Find graph from API
    graph = zapi.graph.get(output="extend", graphids=graphid)

    if graph:
      #print(format(graph))
      # Set width and height
      width = graph[0]['width']
      height = graph[0]['height']

      # Select the right graph generator according to graph type
      # type 3 = Exploded graph
      if graph[0]['graphtype'] == "3":
        generator = "chart6.php"
      # type 2 = Pie graph
      elif graph[0]['graphtype'] == "2":
        generator = "chart6.php"
      # type 1 = Stacked graph
      elif graph[0]['graphtype'] == "1":
        generator = "chart2.php"
      # type 0 = Normal graph
      elif graph[0]['graphtype'] == "0":
        generator = "chart2.php"
      # catch-all in case someone invents a new type/generator
      else:
        generator = "chart2.php"

      # Set login URL for the Frontend (frontend access is needed, as we cannot retrieve graph images via the API)
      loginurl = api + "/index.php"
      # Data that needs to be posted to the Frontend to log in
      logindata = {'autologin' : '1', 'name' : username, 'password' : password, 'enter' : 'Sign in'}
      # We need to fool the frontend into thinking we are a real browser
      headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0', 'Content-type' : 'application/x-www-form-urlencoded'}

      # setup a session object so we can reuse session cookies
      session=requests.session()
      verify=False

      # Login to the frontend
      login=session.post(loginurl, params=logindata, headers=headers, verify=verify)

      # See if we logged in successfully
      try:
        if session.cookies['zbx_sessionid']:

           # Build the request for the graph
           graphurl = api + "/" + generator + "?graphid=" + str(graphid) + "&period=" + str(period)


           # get the graph
           graphreq = session.get(graphurl,verify=verify)
           # read the data as an image
           graphpng = Image.open(StringIO(graphreq.content))
           memf = cStringIO.StringIO()
           graphpng.save(memf, "JPEG")
           return memf

      except:
        sys.exit("Error: Could not log in to retrieve graph")
    else:
        sys.exit("Error: Could not find graphid "+ graphid)


# Arguments parser
parser = argparse.ArgumentParser(description='Send Zabbix notification with Graphics')
parser.add_argument('recipient', metavar=('Recipient'), type=str, help='Email recepient')
parser.add_argument('subject', metavar=('Subject'), type=str, help='Subject you want to push.')
parser.add_argument('message', metavar=('Message'), type=str, help='Message you want to push.')

# Argument processing
args = parser.parse_args()
recipient = args.recipient
subject = args.subject
message = args.message

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

# Define these once; use them twice!
strFrom = 'zabbix_gis_gmp@sitonica.ru'
strTo = recipient

# Create the root message and fill in the from, to, and subject headers
msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = subject
msgRoot['From'] = strFrom
msgRoot['To'] = strTo
msgRoot.preamble = 'This is a multi-part message in MIME format.'

# Encapsulate the plain and HTML versions of the message body in an
# 'alternative' part, so message agents can decide which they want to display.
msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)

msgText = MIMEText('This is the alternative plain text message.')
msgAlternative.attach(msgText)

zapi = ZabbixAPI(url='http://localhost', user='root', password='zabbix123')
zapi.session.verify = False

trig = zapi.trigger.get(output='extend',
  itemids = ['135536','135537'],
  only_true=1,
)

if trig:
  message += "<br><b>Присутствуют проблемы доступа к СМЭВ</b><br>"

# We reference the image in the IMG SRC attribute by the ID we give it below
msgText = MIMEText(message+'<br><img src="cid:image1"><br><br><img src="cid:image2"><br><br><img src="cid:image3"><br>', 'html')
msgAlternative.attach(msgText)

# This example assumes the image is in the current directory
graphImage1 = getGraph(graphid, username, password, api, period)
msgImage1 = MIMEImage(graphImage1.getvalue())
msgImage1.add_header('Content-ID', '<image1>')
msgRoot.attach(msgImage1)

graphImage2 = getGraph(18485, username, password, api, period)
msgImage2 = MIMEImage(graphImage2.getvalue())
msgImage2.add_header('Content-ID', '<image2>')
msgRoot.attach(msgImage2)

graphImage3 = getGraph(11706, username, password, api, period)
msgImage3 = MIMEImage(graphImage3.getvalue())
msgImage3.add_header('Content-ID', '<image3>')
msgRoot.attach(msgImage3)

# Send the email (this example assumes SMTP authentication is required)

import smtplib
smtp = smtplib.SMTP('localhost', 25)
smtp.ehlo()
smtp.sendmail(strFrom, strTo, msgRoot.as_string())
smtp.quit()
