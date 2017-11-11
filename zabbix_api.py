#!/usr/local/bin/python3.4
from slack_zabbix import *

class Zabbix_api(Zabbix,):
    # def __init__(self, ):
    #     req_headers = {
    #         'Content-Type': 'application/json-rpc'
    #     }


    def authorization(self, ):
        """ login in api, returh auth string"""
        req_headers = {
            'Content-Type': 'application/json-rpc'
        }

        # payload for typing form
        formdata = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.auth['user'],
                "password": self.auth['password']
                        },
            "id": 1,
                    }
        form = json.dumps(formdata)
        session = requests.session()
        # Authenticate at zabbix frontend
        r = session.post(self.auth['zabbix_api'], data=form,
                         headers=req_headers)
        j = json.loads(r.text)
        return(j['result'])



    def problem_last_trigger_get(self, auth):
        ''' Return dict wit last 20 issue'''
        session = requests.session()
        req_headers = {
            'Content-Type': 'application/json-rpc'
            }
        data = {
            "jsonrpc": "2.0",
            "method": "trigger.get",
            "params": {
                "filter": {"value": "1"},
            # select interesting value
            "selectHosts":['description', 'host', 'error'],
            "sortfield": "lastchange",
                "limit": 20,
                },
            "auth": auth,
            "id": 1
                    }
        form = json.dumps(data)
        r = session.post(self.auth['zabbix_api'], data=form, headers=req_headers)
        return(r)


    def logout(self, auth):
        """ logout from api"""
        req_headers = {
            'Content-Type': 'application/json-rpc'
        }

        # payload for typing form
        formdata = {
            "jsonrpc": "2.0",
            "method": "user.logout",
            "params": [],
            "id": 1,
            "auth" : auth,
                    }
        form = json.dumps(formdata)
        session = requests.session()
        # Authenticate at zabbix frontend
        r = session.post(self.auth['zabbix_api'], data=form,
                         headers=req_headers)




    def attract(self, ):
        auth = Zabbix_api().authorization()
        dicttr = Zabbix_api().problem_last_trigger_get(auth).json()
        phrase = str()
        for i in range(20):
            try:
                if dicttr['result'][i]['status'] == '1':
                    pass
                else:
                    phrase += '\n' + dicttr['result'][i]['hosts'][0]['host'] + \
                    ' ' + dicttr['result'][i]['description']+ \
                    ' ' + dicttr['result'][i]['hosts'][0]['error']
            except IndexError:
                print('list out of range')
        Slack().send_event(phrase)
        Zabbix_api().logout(auth)


if __name__ == '__main__':
    Zabbix_api().attract()
