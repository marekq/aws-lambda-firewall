#!/usr/bin/python
# marek.kuczynski
# @marekq
# www.marek.rocks

import requests, sys

# enter the API key provided by your API gateway
k 	= {'x-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}

# enter the URL used by your API gateway
u	= 'https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com'

if len(sys.argv) != int(5):
	ip 	= '127.0.0.1'
	po	= '22'
	du	= int('1')
	pr	= 'tcp'


##### do not touch anything below this line #####
else:
	ip	= sys.argv[1]
	po	= sys.argv[2]
	du	= sys.argv[3]
	pr	= sys.argv[4]


def get_ip(ip):
    if len(ip) == 0:
        r               = requests.get('http://ipinfo.io/ip', timeout=5)

        if r.status_code == int(200):
            cidr_ip     = r.text.strip()
        else:
            cidr_ip     = ''
    else:
        cidr_ip         = ip

    return str(cidr_ip)

def get_port(po):
	return str(po)

def get_dura(du):
	d	= int(du) * int(60)
	return str(d)

def get_proto(pr):
	if len(pr) == 0:
		return 'tcp'
	else:
		return pr

def whitelist():
	i	= get_ip(ip)
	p	= get_port(po)
	d	= get_dura(du)
	t	= get_proto(pr)

	q	= '/prod/firewall?ip='+i+'&port='+p+'&duration='+d+'&proto='+t

	r 	= requests.get(u+q, headers = k)
	print r.content

whitelist()
