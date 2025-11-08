import os
from dotenv import load_dotenv

load_dotenv()
import python_bithumb
import json
import csv
import time
from datetime import datetime
import requests
from openai import OpenAI
from prompts import TRADING_PROMPT


# CSV 파일 경로
TRADE_HISTORY_FILE = "trade_history.csv"

# CSV 파일이 없으면 헤더 생성
if not os.path.exists(TRADE_HISTORY_FILE):
    with open(TRADE_HISTORY_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["datetime", "decision", "reason", "fear_and_greed", "krw_balance", "btc_balance", "btc_price", "total_asset", "action_result"])


def ai_trading():
    # 1. 빗썸 차트 데이터 가져오기 (30일 일봉)
    df = python_bithumb.get_ohlcv("KRW-BTC", interval="minutes15", count=30)

    # 공포 탐욕지수 가져오기
    fearAndGreed = requests.get("https://api.alternative.me/fng/").json()['data'][0]
    print(fearAndGreed)

    # 2. AI 판단 요청
    client = OpenAI()
    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": TRADING_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""Daily OHLCV with indicators (30 days): {df.to_json()},
Fear and Greed Index: {fearAndGreed}"""
                    }
                ]
            }
        ],
        text={"format": {"type": "json_object"}, "verbosity": "low"},
        reasoning={"effort": "minimal"},
        tools=[],
        store=False
    )

    result = response.output[1].content[0].text
    result = json.loads(result)

    # 3. 실제 매매 진행
    access = os.getenv("BITHUMB_ACCESS_KEY")
    secret = os.getenv("BITHUMB_SECRET_KEY")
    bithumb = python_bithumb.Bithumb(access, secret)

    my_krw = bithumb.get_balance("KRW")
    my_btc = bithumb.get_balance("BTC")

    # BTC 현재가 가져오기
    current_price = python_bithumb.get_current_price("KRW-BTC")
    # 총자산 계산
    total_asset = my_krw + (my_btc * current_price)

    print("### AI Decision:", result["decision"], "###")
    print(f"### Reason: {result['reason']} ###")

    action_result = ""

    if result["decision"] == "buy":
        if my_krw > 5000:
            bithumb.buy_market_order("KRW-BTC", 10000)
            action_result = "Buy Executed (10,000 KRW)"
        else:
            action_result = "Buy Failed: Insufficient KRW (<5000 KRW)"

    elif result["decision"] == "sell":
        if my_btc * current_price > 5000:
            bithumb.sell_market_order("KRW-BTC", 0.00007)
            action_result = f"Sell Executed (0.00007 BTC)"
        else:
            action_result = "Sell Failed: Insufficient BTC (<5000 KRW worth)"

    elif result["decision"] == "hold":
        action_result = "Hold Position"

    print("###", action_result, "###")

    # 4. CSV 로그 기록
    with open(TRADE_HISTORY_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            result["decision"],
            result["reason"],
            fearAndGreed["value"],
            my_krw,
            my_btc,
            current_price,
            total_asset,
            action_result
        ])


# 5. 3시간마다 실행 (10800초)
while True:
    ai_trading()
    time.sleep(5)