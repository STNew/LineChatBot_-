import requests
import re
import random
import configparser
from bs4 import BeautifulSoup
from flask import Flask, request, abort
from imgurpython import ImgurClient
import json
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

from flask import  render_template
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand



app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
client_id = config['imgur_api']['Client_ID']
client_secret = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_ID']
API_Get_Image = config['other_api']['API_Get_Image']

# Database 設立之相關程式碼 ↓↓↓↓↓↓↓↓↓↓
app.config['SQLALCHEMY_DATABASE_URI'] ='你的Data Base URI'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

#Database 模擬貨物狀況
class packagesData(db.Model):
    __tablename__ = 'packagesData'

    Id = db.Column(db.Integer, primary_key=True)
    PackagesId = db.Column(db.String(64))
    PackState = db.Column(db.String(256))
    def __init__(self
                 , PackagesId
                 , PackState
                 ):
        self.PackagesId = PackagesId
        self.PackState = PackState

#Data Base 紀錄對話紀錄
class userData(db.Model):  
    __tablename__ = 'userData'

    Id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(64))
    TextRecord = db.Column(db.String(256))
    DateTime=db.Column(db.BigInteger)

    def __init__(self
                 , Name
                 , TextRecord
                 , DateTime
                 ):
        self.Name = Name
        self.TextRecord = TextRecord
        self.DateTime=DateTime

db.create_all()
#範例資料建立
add_data0 = packagesData(PackagesId='101',PackState='運送中')
db.session.add(add_data0)
db.session.commit()
add_data = userData(Name='991',TextRecord='我還沒開始說',DateTime=1000)
db.session.add(add_data)
db.session.commit()
# Database 設立之相關程式碼↑↑↑↑↑↑↑↑↑


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'




@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    print("event.source.user_id:", event.source.user_id)  
    print("event.timestamp:", event.timestamp) 
    input_text=event.message.text
    beforeText=userData.query.filter(userData.Name==event.source.user_id).order_by(userData.DateTime.desc()).first()
    if beforeText is not None:
        if (input_text == "我的貨物單號是：" ) :
            UserText=userData(Name=event.source.user_id,TextRecord=input_text,DateTime=event.timestamp)
            db.session.add(UserText)
            db.session.commit()
            return 0   
        print("beforeText.TextRecord:", beforeText.TextRecord) 
        if (beforeText.TextRecord == "我的貨物單號是：")  :
            UserText=userData(Name=event.source.user_id,TextRecord=input_text,DateTime=event.timestamp)
            db.session.add(UserText)
            db.session.commit()
            state=packagesData.query.filter(packagesData.PackagesId==input_text).first()
            if (state is not None):
                # print('--type(state.Name): ',type(state.Name))
                # print("--state.Name: ",state.Name)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=str(state.PackState)))
                return 0
            else:
                buttons_template = TemplateSendMessage(
                    alt_text='開始玩 template',
                    template=ButtonsTemplate(
                        title='查無此包裹',
                        text='請問您需要什麼服務',
                        thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                        actions=[
                            MessageTemplateAction(
                                label='單號查詢包裹',
                                text='我的貨物單號是：'
                            ),
                            MessageTemplateAction(
                                label='沒事了',
                                text=' '
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, buttons_template)
                return 0

    
    UserText=userData(Name=event.source.user_id,TextRecord=input_text,DateTime=event.timestamp)
    db.session.add(UserText)
    db.session.commit()
    buttons_template = TemplateSendMessage(
        alt_text='開始玩 template',
        template=ButtonsTemplate(
            title='選擇查詢包裹方式',
            text='請選擇',
            thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
            actions=[
                MessageTemplateAction(
                    label='單號查詢包裹',
                    text='我的貨物單號是：'
                ),
                MessageTemplateAction(
                    label='收件人資訊查詢包裹',
                    text='收件人資訊查詢包裹**'
                ),
                MessageTemplateAction(
                    label='沒事',
                    text=' '
                )
            ]
        )
    )
    line_bot_api.reply_message(event.reply_token, buttons_template)
    return 0



@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("package_id:", event.message.package_id)
    print("sticker_id:", event.message.sticker_id)
    # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    print(index_id)
    sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id=sticker_id
    )
    line_bot_api.reply_message(
        event.reply_token,
        sticker_message)


if __name__ == '__main__':
    app.run()
