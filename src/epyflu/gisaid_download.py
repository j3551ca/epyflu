import requests
import re
import gisflu
import json
import urllib.parse
import hashlib
import time

#explore how gisflu based on GISAIDR works.
# 
# session id, window id stays consistent - component & process ids change and are acquired from payload
# after post sent and get received.
#  
# url = "https://gisaid.org/"
url = "https://platform.epicov.org/epi3/frontend?"

response = requests.get(url)

sid_match = re.search(r'name="sid"\s+value=\'([^\']*)\'', response.text)
sid = sid_match.group(1)

login_page = requests.get(url, "sid="+sid)

wid_match =  re.search(r'sys\["WID"\] = "(.+?)";', login_page.text)
wid = wid_match.group(1)

pid_match =  re.search(r'sys\["PID"\] = "(.+?)";', login_page.text)
pid = pid_match.group(1)

cid_match =  re.search(r"sys\.getC\(\'(.+?)\'\).call\(\'doLogin", login_page.text)
cid = cid_match.group(1)
# login_page.text
# cid

# search payload
# pid_match =  re.search(r'name="pid"\s+value=\'([^\']*)\'', response.text)
# pid = pid_match.group(1)
# print(sid)

# response2 = requests.get('sid='+ sid)
# print(match.group(1))
# print(re.search("sid",str(response.content)))
# print(re.search(r'name="sid" value="([^"]+)"',str(response.content)))
# response.text
password_md5 = hashlib.md5(password.encode()).hexdigest()

# r = requests.get(url, auth=("", ""))
# print(r.request.headers["Authorization"])

command = [{
      "cid": cid,
      "cmd": "doLogin",
      "params": {"login": username, "hash": password_md5},
      "equiv": None
}]

not_sure = {"queue": [{"wid": wid, "pid": pid, **d} for d in command]}
json_command = json.dumps(not_sure)

timestamp = str(int(time.time() * 1000))
mode = "ajax"
ask = {
    "sid": sid,
    "wid": wid,
    "pid": pid,
    "data": json_command,
    "ts": timestamp,
    "mode": mode
}

# this was key 
encoded_ask = urllib.parse.urlencode(ask)
#base64 encoding is a way to convert binary data (images, websites, etc.) into text using 64 ASCII characters (aA-zZ,0-9,+,/)
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}

logged_in = requests.post(url, data=ask, headers=headers)
first_page = logged_in.text

# cms_page string means you are in
assert re.search("cms_page", first_page), "Username or password wrong!"


# import base64
# import requests

# # Extracting and decoding the "back" parameter
# back_encoded = 'eyJzaWQiOiAiQ0ZEQTlDNlhEWkJRUEJaWDk5MDNRWEhYUFFQQVA3VDYiLCAibW9kZSI6ICJwYWdlIiwgIl91cmwiOiAiaHR0cHM6Ly9wbGF0Zm9ybS5lcGljb3Yub3JnL2VwaTMvZnJvbnRlbmQifQ=='
# back_decoded = base64.b64decode(back_encoded).decode('utf-8')
# print("Decoded back parameter:", back_decoded)

# # Reconstructing the POST request
# url = 'https://www.epicov.org/epi3/cfrontend'
# params = {
#     'cms_page': 'corona2020',
#     'back': back_encoded,
#     'sid': '2BDEE5CM1DUQSWSHA4E2NBSZX5LAW756',
#     'mode': 'page'
# }

# response = requests.post(url, data=params)
# print("Response from the POST request:", response.text)

receipt = requests.get(f"{url}sid={sid}", headers)
first_page_info = receipt.text

def get_id(search_str, webpage):
    """
    Get the value of process, window, component, session id.
    regex used must enclose desired value as group (.+?).
    
    """
    match = re.search(search_str, webpage)
    return match.group(1)

pid_first_page = get_id(r'sys\["PID"\] = "(.+?)";',
                        first_page_info)
cid_first_page = get_id(r"sys.getC\(\'(.+?)\'\).call\(\'doLogin\'",
                        first_page_info)
wid_first_page = get_id(r'sys\["WID"\] = "(.+?)";', 
                        first_page_info)

# new_wid? = wid_siifsf_2byk
command = [{
      "cid": cid_first_page,
      "cmd": 'Go',
      "params": {"page":"epi3"},
      "equiv": None
}]

not_sure = {"queue": [{"wid": wid_first_page, "pid": pid_first_page, **d} for d in command]}
json_command = json.dumps(not_sure)

timestamp = str(int(time.time() * 1000))
mode = "ajax"
ask = {
    "sid": sid,
    "wid": wid_first_page,
    "pid": pid_first_page,
    "data": json_command,
    "ts": timestamp,
    "mode": mode
}

# this was key 
encoded_ask = urllib.parse.urlencode(ask)

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}

res = requests.post(url, data=ask, headers=headers)
flu_home = res.text


flu_home_pid = get_id(r"sys.goPage\(\'(.+?)\'\)", flu_home)

#retrieve flu db home webpage get = receive, post = send
receipt = requests.get(f"{url}sid={sid}&pid={flu_home_pid}", headers=headers)
flu_db_homepage = receipt.text
flu_db_homepage


cred = gisflu.login()



gisaid_df = gisflu.search(cred, 
              searchPattern="British_Columbia",
              submitDateFrom="2023-12-31",
              recordLimit=50000)

