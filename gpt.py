import requests
import json
import os
import time

API_KEY = os.getenv("BAIDU_API_KEY")
SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
BAIDU_ACCESS_TOKEN_API = "https://aip.baidubce.com/oauth/2.0/token"
MODEL_API = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/chatglm2_6b_32k"
if API_KEY is None or SECRET_KEY is None:
    raise ValueError("BAIDU_API_KEY, BAIDU_SECRET_KEY 不能为空")

basedir = os.path.dirname(os.path.abspath(__file__))


def get_access_token():
    """
    获取百度云OCR API的access_token
    :return: access_token
    """
    flag = False
    try:
        with open(os.path.join(basedir, "access_token.json"), "r") as f:
            d = json.load(f)
    except FileNotFoundError:
        flag = True
    else:
        if d["expires_time"] < int(time.time()):
            flag = True
    if flag:
        r = requests.post(BAIDU_ACCESS_TOKEN_API, params={
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": SECRET_KEY
        }, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }, data="")
        d = dict()
        d["access_token"] = r.json()["access_token"]
        d["expires_time"] = r.json()["expires_in"] + int(time.time())
        with open(os.path.join(basedir, "access_token.json"), "w") as f:
            json.dump(d, f, ensure_ascii=False)
    return d["access_token"]


def chat_with_model(msgs, user_id):
    """
    使用百度云自定义模型API进行对话
    :param text: 对话内容
    :return: 返回对话结果
    """
    access_token = get_access_token()
    r = requests.post(MODEL_API, params={
        "access_token": access_token
    }, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }, data=json.dumps({
        'user_id': user_id,
        'messages': msgs
    }))
    return r.json()["result"]
