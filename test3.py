import requests
from bs4 import BeautifulSoup

headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0'
}
# login = '01WuK8'
# password = '1V639R'
# ip = '185.68.187.246'
# port = '8000'

login = 'ynhYd9'
password = 'xbkGc5'
ip = '45.134.186.67'
port = '8000'
proxies = {
	# 'https': 'http://proxy_ip:proxy_port'
	# 'https': f'http://{ip}:{port}'
	'https': f'http://{login}:{password}@{ip}:{port}'
}


data = requests.get('https://ipinfo.io/json', headers=headers, proxies=proxies)

print(data.text)

#
# def get_location(url):
# 	response = requests.get(url=url, headers=headers, proxies=proxies)
# 	soup = BeautifulSoup(response.text, 'lxml')
#
# 	ip = soup.find('div', class_='ip').text.strip()
# 	location = soup.find('div', class_='value-country').text.strip()
#
# 	print(f'IP: {ip}\nLocation: {location}')
#
#
# def main():
# 	get_location(url='https://2ip.ru')
#
#
# if __name__ == '__main__':
# 	main()
