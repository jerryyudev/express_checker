import requests
import json
import telegram

def send_telegram_message(bot_token, chat_id, message):
    """发送 Telegram 消息"""
    try:
        bot = telegram.Bot(token=bot_token)
        bot.send_message(chat_id=chat_id, text=message)
        print(f"消息已成功发送至 TGID: {chat_id}")
    except Exception as e:
        print(f"发送 Telegram 消息失败: {e}")

def format_express_data(data):
    """格式化快递信息"""
    formatted_message = "【快递信息】\n\n"
    if "data" in data and "context" in data["data"]:
        formatted_message += "物流轨迹:\n"
        for item in data["data"]["context"]:
            formatted_message += f"- 时间: {item['time']}, 地点/描述: {item['desc']}\n"
        formatted_message += "\n"
    if "data" in data and "officalService" in data["data"]:
        formatted_message += "官方信息:\n"
        formatted_message += f"- 公司名称: {data['data']['officalService']['comName']}\n"
        formatted_message += f"- 官方电话: {data['data']['officalService']['servicePhone']}\n"
        formatted_message += f"- 官网地址: {data['data']['officalService']['url']}\n"
        if "service" in data["data"]["officalService"]:
            formatted_message += "更多服务:\n"
            for service in data["data"]["officalService"]["service"]:
                formatted_message += f"  - {service['name']}: {service['url']}\n"
    elif "msg" in data:
        formatted_message += f"错误信息: {data['msg']}\n"
    else:
        formatted_message += "未能解析快递信息。\n"
    return formatted_message

def fetch_express_data(url, headers):
    """发送 curl 请求获取快递数据"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        # 处理 JSONP 格式的数据
        content = response.text.replace("jsonp_1745405091346_59609(", "").replace(")", "")
        data = json.loads(content)
        return data
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return None

if __name__ == "__main__":
    url = "https://alayn.baidu.com/express/appdetail/pc_express?query_from_srcid=51150&tokenV2=wzUQQuOXKkbBg0u4CvHGef1li4jp3iqIk1UITh7%2FVopP15dPsO%2FdP%2FemO6EEmxr6&com=shentong&nu=773350868039582&qid=bdd4518e000080d4&cb=jsonp_1745405091346_59609"
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cookie": "BDUSS=M1elRwSUdEUkVQNGMyOUNxMkN4U2QwcnVJaWJGcWs2OWQ3NE81fkZhVW43Z1JvRVFBQUFBJCQAAAAAAQAAAAEAAABntqkMzuXOrL~VvOQ2NjY2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACdh3WcnYd1ndH; BDUSS_BFESS=M1elRwSUdEUkVQNGMyOUNxMkN4U2QwcnVJaWJGcWs2OWQ3NE81fkZhVW43Z1JvRVFBQUFBJCQAAAAAAQAAAAEAAABntqkMzuXOrL~VvOQ2NjY2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACdh3WcnYd1ndH; PSTM=1742564148; BAIDUID=79FCA02E0250A59156351BF08691ACE7:SL=0:NR=10:FG=1; MCITY=-131%3A; H_WISE_SIDS_BFESS=61027_62342_62327_62677_62721_62848_62878_62881_62885_62919_62921_62968; BIDUPSID=1F6975F965D32D3F99F05F3E76C74890; H_WISE_SIDS=61027_62342_62327_62677_62721_62878_62881_62885_62919_62921_62968; H_PS_PSSID=61027_62342_62327_62721_62878_62881_62885_62968_63041_63045; BAIDUID_BFESS=79FCA02E0250A59156351BF08691ACE7:SL=0:NR=10:FG=1; ab_sr=1.0.1_NWRkZjdlNmY3NmE2ZDkyYjQ1OWU4NTk1YjFkN2RhODk5YjJhYjlhMGE5NDkyMDFiODJkZTQ3ZjQ0Nzk1NDlkZWE1ZTZhYTAzZGI4NWMyYzFjZTUzYmNlZDExNWJhNjQwYmFlOWY0NTU1OTUzMzM2OTAwYTVjYWZlNWMwYjE4MjI5ZGJmNzM1NDlhYjk1YTg1NTg4YmE5NjFjNjhlYTQ1NDU5YjA3NzE1YTIwZTkyMTU2YjZjMGE5OTFmMWM0YzMx; RT=\"z=1&dm=baidu.com&si=b1ddcf3c-3eb2-4959-865d-2bf46b642e82&ss=m9tt3yvf&sl=1&tt=2it&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=3ds\"",
        "referer": "https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd=773350868039582&fenlei=256&rsv_pq=0x8fec8a15001e861a&rsv_t=8ec1WXBdhga%2F8%2Ft9E92aHj9FbmumqtAOyWwv3GblnfRqRAreRg%2FueTi%2F%2Brj%2B&rqlang=en&rsv_enter=1&rsv_dl=tb&rsv_sug3=2&rsv_n=2&rsv_sug2=0&rsv_btype=i&inputT=1138&rsv_sug4=1274",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15 Edg/131.0.0.0"
    }
    bot_token = "7394878059:AAHS8AOQ4Y9cnIhoO2j-o8cQnKhTZUWq3K4"
    target_tg_id = "7854789916"

    express_data = fetch_express_data(url, headers)

    if express_data:
        formatted_message = format_express_data(express_data)
        send_telegram_message(bot_token, target_tg_id, formatted_message)
    else:
        send_telegram_message(bot_token, target_tg_id, "获取快递信息失败。")
