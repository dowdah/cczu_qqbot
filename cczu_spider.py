import requests
from bs4 import BeautifulSoup
import time

PE_CLOCKIN_NUM_CHECK_URL = 'http://202.195.100.156:808/result.aspx'
PE_CLOCKIN_NUM_CHECK_TIME_OUT = 60
PE_CLOCKIN_NUM_CHECK_ERROR_MSG = "错误: 与学校查询网站通讯失败，请稍后再试。"
TID_FOR_PE_CLOCKIN = '81'


def get_pe_clockin_info(stu_id):
    """
    Get the number of PE clock-in
    :param stu_id: student id
    :return: number of PE clock-in
    """
    try:
        r = requests.get(PE_CLOCKIN_NUM_CHECK_URL, params={'sno': stu_id, 'tid': TID_FOR_PE_CLOCKIN},
                         timeout=PE_CLOCKIN_NUM_CHECK_TIME_OUT)
    except requests.exceptions.Timeout:
        return PE_CLOCKIN_NUM_CHECK_ERROR_MSG
    if r.status_code != 200:
        return PE_CLOCKIN_NUM_CHECK_ERROR_MSG
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        c_i = [s.text.strip() for s in soup.find_all('div', class_='div_container')[0].find_all('tr')[1].find_all('td')]
    except IndexError:
        return "错误: 你自己看看你的学号正确吗？重新绑定！"
    # c_i stands for clockin info
    str_clockin_info = f"你好，{c_i[1]}({c_i[0]})。你本学期活动次数为{c_i[3]}次，有效次数{c_i[4]}次。本学期及格要求次数为{c_i[5]}次，你的结果为{c_i[6]}。"
    return str_clockin_info


if __name__ == '__main__':
    t1 = time.time()
    print(get_pe_clockin_info('2300160426'))
    print(time.time() - t1)
