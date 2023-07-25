import requests
import time


def get_answer(question):
    url = 'https://chat.jinshutuan.com/#/chat/1690249865632'  # 替换成实际的网址
    data = {'question': question}  # 替换成实际的请求参数

    response = requests.post(url, data=data)
    time.sleep(10)  # 等待10秒钟

    return response.text  # 返回答案


question = input('请输入问题：')
answer = get_answer(question)
print('答案：', answer)
