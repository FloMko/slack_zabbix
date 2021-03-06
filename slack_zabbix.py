#!/usr/local/bin/python3.4
"""slack-zabbix MODULE."""
# basik lib emulate http client
import requests
# parser cli argument
import argparse
# metalanguage lineup
import yaml
# serialize request
import json
# find in body item
import re


def cli_args():
    """CLI Argument Parser."""
    parser = argparse.ArgumentParser(prog='zabbix slack script')
    parser.add_argument('channel', nargs=1)
    parser.add_argument('subject', nargs=1)
    parser.add_argument('body', nargs=1)
    args = parser.parse_args()
    return {

        'channel': args.channel[0],
        'subject': args.subject[0],
        'body': args.body[0],
    }


def parse_configs(path):
    """Parse configuration YAML configuration file."""
    try:
        with open(path) as cfg:
            config = yaml.load(cfg.read())
    except FileNotFoundError:
        path = '/usr/local/etc/zabbix3/zabbix/alertscripts/slack_zabbix.cfg'
        with open(path) as cfg:
            config = yaml.load(cfg.read())
    return config


class Zabbix(object,):
    """ Class for iteraction with
    Zabbix Communication."""
    def __init__(self,  config_path = './slack_zabbix.cfg'):
        config = parse_configs(config_path)
        self.auth={}
        self.auth['user'] = config['auth']['user']
        self.auth['password'] = config['auth']['password']
        self.auth['zabbix_url'] = config['auth']['zabbix_url']
        self.auth['zabbix_api'] = config['auth']['zabbix_api']
        # header for api requests
        req_headers = {
            'Content-Type': 'application/json-rpc'
        }


    def get_image(self, zbx_img_url ):
        LOGINURL = self.auth['zabbix_url']
        DATAURL = zbx_img_url
        # setencoding (also can raw work with urllib)
        req_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # payload for typing form
        formdata = {
            'name': self.auth['user'],
            'password': self.auth['password'],
            'enter': 'Sign in',
            'form_refresh': '1',
        }
        session = requests.session()
        # Authenticate at zabbix frontend
        r = session.post(self.auth['zabbix_url'], data=formdata,
                         headers=req_headers, allow_redirects=False)
        # open php dynamick graph and save
        r2 = session.get(DATAURL)
    # write to file
        with open('/tmp/zabbix.png', 'wb') as f:
            f.write(r2.content)


    def find_item(self, body):
        """ find item id by spec body message"""
        settings = {
            "zbx_itemid": "0",  # itemid for graph
            "zbx_title": None,  # title for graph
            "zbx_trigger": None,
            "zbx_itemname": None,
        }
        settings_description = {
            "itemid": {"name": "zbx_itemid", "type": "int"},
            "title": {"name": "zbx_title", "type": "str"},
            "trigger": {"name": "zbx_trigger", "type": "str"},
            "itemname": {"name": "zbx_itemname", "type": "str"},
        }
        # append body to line
        zbx_body = (body).splitlines()
        zbx_body_text = []
        for line in zbx_body:
            if line.find('zbx') > -1:
                setting = re.split("[\s\:\=]+", line, maxsplit=1)
                key = setting[0].replace('zbx' + ";", "")
                if len(setting) > 1 and len(setting[1]) > 0:
                    value = setting[1]
                else:
                    value = True
                if key in settings_description:
                    settings[settings_description[key]["name"]] = value

            else:
                zbx_body_text.append(line)
        # return(settings['zbx_trigger'], settings['zbx_title'])
        zbx_img_url = Zabbix.get_image_id(self, settings['zbx_title'], settings['zbx_itemid'])
        return(zbx_img_url)


    def get_image_id(self, hostname, itemid):
        """Atraction to zabbix api to know graph id"""
        name = hostname
        # name_item = trigername
        item = itemid
        zbx_img_url = 'https://bigbro.m10m.ru/zabbix/chart3.php?period=900&name=' + str(name) \
            + '&width=900&height=300&graphtype=0&legend=1&items[0][itemid]=' \
             + str(item) + '&items[0][sortorder]=0&items[0][drawtype]=5&items[0][color]=00CC00'
        return(zbx_img_url)


class Slack(object):

    """Class for Slack API"""

    def __init__(self, config_path='./slack_zabbix.cfg'):
        """
        Construct class.
        Constructor Arguments in kwargs and configuration
        file './slack_zabbix.cfg'.
        """
        config_path = config_path if config_path is not None \
            else '/usr/local/etc/zabbix3/zabbix/alertscripts/slack_zabbix.cfg'
        config = parse_configs(config_path)
        self.emoji = {}
        self.emoji['recovery'] = config['emoji']['recovery']
        self.emoji['problem'] = config['emoji']['problem']
        self.emoji['default'] = config['emoji']['default']
        self.slack = {}
        self.slack['token'] = config['slack']['token']


    def send_event(self, message):
        """Send request to slack BE."""
        i = 0
        while i < 6:
            try:
                data={'token':self.slack['token'], 'channel':'#zabbix', 'text':message}
                resp = requests.post(
                    'https://slack.com/api/chat.postMessage',
                    data=data,
                )
            except requests.exceptions.Timeout:
                i += 1
                continue
            if 199 < resp.status_code < 299:
                return True, resp.content
            else:
                return False, resp.content
        return False, 'API timed out too many times'


    def post_image(self,):
        """Posting image to channel"""
        filename = '/tmp/zabbix.png'
        channels ='#zabbix'
        token = self.slack['token']
        f = {'file': (filename, open(filename, 'rb'), 'image/png', {'Expires':'0'})}
        response = requests.post(url='https://slack.com/api/files.upload',
            data={'token': token, 'channels': channels, 'media': f},
            headers={'Accept': 'application/json'}, files=f)


class Attraction(object):
    """basik unit action
    """
    def broadcast(self, **kwargs):
        # """Entry point function."""
        channel = kwargs.get('channel', '#general')
        subject = kwargs.get('subject', 'ERROR')
        body = kwargs.get(
            'body',
            'Zabbix did not provide a message body'
        )
        message = '{0}: {1}'.format(subject, body)
        Slack().send_event(message)
        zbx_img_url = Zabbix().find_item(body)
        Zabbix().get_image(zbx_img_url)
        Slack().post_image()


if __name__ == '__main__':
    ARGS = cli_args()
    Attraction().broadcast(**ARGS)

