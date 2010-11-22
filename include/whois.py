# -*- coding: utf-8 -*-
# whois.py - Module for parsing whois response data
# Copyright (c) 2008 Andrey Petrov
#
# This module is part of pywhois and is released under
# the MIT license: http://www.opensource.org/licenses/mit-license.php
#
# minor changes and new parsers by MatToufoutu
#
#TODO: code parser for .uk domains

import re
import time
from subprocess import Popen, PIPE
from sys import argv, exit as sysexit
try:
    set
except NameError:
    from sets import Set as set


SUFFIXES = (
    'ac', 'ad', 'ae', 'aero', 'af', 'ag', 'ai', 'al', 'am',
    'an', 'ao', 'aq', 'ar', 'arpa', 'as', 'asia', 'at', 'au',
    'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh',
    'bi', 'biz', 'bj', 'bm', 'bn', 'bo', 'br', 'bs', 'bt', 'bv',
    'bw', 'by', 'bz', 'ca', 'cat', 'cc', 'cd', 'cf', 'cg', 'ch',
    'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'com', 'coop', 'cr', 'cu',
    'cv', 'cx', 'cy', 'cz', 'de', 'dj', 'dk', 'dm', 'do', 'dz',
    'ec', 'edu', 'ee', 'eg', 'er', 'es', 'et', 'eu', 'fi', 'fj', 'fk',
    'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi',
    'gl', 'gm', 'gn', 'gov', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw',
    'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im',
    'in', 'info', 'int', 'io', 'iq', 'ir', 'is', 'it', 'je', 'jm',
    'jo', 'jobs', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr',
    'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt',
    'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mg', 'mh', 'mil', 'mk',
    'ml', 'mm', 'mn', 'mo', 'mobi', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu',
    'mv', 'mw', 'mx', 'my', 'mz', 'na', 'name', 'nc', 'ne', 'net', 'nf',
    'ng', 'ni', 'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'org', 'pa',
    'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr', 'pro', 'ps',
    'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc',
    'sd', 'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr',
    'st', 'su', 'sv', 'sy', 'sz', 'tc', 'td', 'tel', 'tf', 'tg', 'th', 'tj',
    'tk', 'tl', 'tm', 'tn', 'to', 'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua',
    'ug', 'uk', 'us', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu',
    'wf', 'ws', 'xn', 'ye', 'yt', 'za', 'zm', 'zw',
)


class WhoisError(Exception):
    pass


class WhoisEntry(object):
    """
    Base whois entries parser class.
    """
    regex = {
        'domain_name':      'Domain Name:\s?(.+)',
        'registrar':        'Registrar:\s?(.+)',
        'whois_server':     'Whois Server:\s?(.+)',
        'referral_url':     'Referral URL:\s?(.+)',
        'updated_date':     'Updated Date:\s?(.+)',
        'creation_date':    'Creation Date:\s?(.+)',
        'expiration_date':  'Expiration Date:\s?(.+)',
        'name_servers':     'Name Server:\s?(.+)',
        'status':           'Status:\s?(.+)',
        'emails':           '[\w.-]+@[\w.-]+\.[\w]{2,4}',
    }

    def __init__(self, domain, text, regex=None):
        self.domain = domain
        self.text = text
        if regex is not None:
            self.regex = regex

    def __getattr__(self, attr):
        """
        The first time an attribute is called it will be calculated here.
        The attribute is then set to be accessed directly by subsequent calls.
        """
        whois_regex = self.regex.get(attr, None)
        if whois_regex is not None:
            whois_regex = re.compile(whois_regex)
            results = set(whois_regex.findall(self.text))
            results = [r for r in results if r.strip()] if results else None
            setattr(self, attr, results)
            return getattr(self, attr)
        else:
            raise KeyError('Unknown attribute: %s' % attr)

    def __str__(self):
        """
        Return all whois properties of domain in string format.
        """
        return '\n'.join('%s: %s' % (attr, str(getattr(self, attr))) for attr in self.attrs)

    @property
    def attrs(self):
        """
        Return a list of attributes that can be extracted for this domain.
        """
        return sorted(self.regex.keys())

    @staticmethod
    def load(domain, text):
        """
        Given a whois output string, return a WhoisEntry instance representing the parsed content.
        """
        #TODO: find a way to make these calls dynamics
        if text.strip() == 'No whois server is known for this kind of object.':
            raise WhoisError(text)
        if domain.endswith('.com'):
            return WhoisCom(domain, text)
        elif domain.endswith('.net'):
            return WhoisNet(domain, text)
        elif domain.endswith('.org'):
            return WhoisOrg(domain, text)
        elif domain.endswith('.ru'):
            return WhoisRu(domain, text)
        elif domain.endswith('.name'):
            return WhoisName(domain, text)
        elif domain.endswith('.us'):
            return WhoisUs(domain, text)
        elif domain.endswith('.me'):
            return WhoisMe(domain, text)
        elif domain.endswith('.fr'):
            return WhoisFr(domain, text)
        elif domain.endswith('.it'):
            return WhoisIt(domain, text)
        elif domain.endswith('.uk'):
            return WhoisUk(domain, text)
        else:
            return WhoisEntry(domain, text)


class WhoisCom(WhoisEntry):
    """
    Whois parser for .com domains.
    """
    def __init__(self, domain, text):
        if 'No match for "' in text:
            raise WhoisError(text)
        else:
            super(WhoisCom, self).__init__(domain, text)


class WhoisNet(WhoisEntry):
    """
    Whois parser for .net domains.
    """
    def __init__(self, domain, text):
        if 'No match for "' in text:
            raise WhoisError(text)
        else:
            super(WhoisNet, self).__init__(domain, text)


class WhoisOrg(WhoisEntry):
    """
    Whois parser for .org domains.
    """
    def __init__(self, domain, text):
        if text.strip() == 'NOT FOUND':
            raise WhoisError(text)
        else:
            super(WhoisOrg, self).__init__(domain, text)


class WhoisRu(WhoisEntry):
    """
    Whois parser for .ru domains.
    """
    regex = {
        'domain_name':      'domain:\s*(.+)',
        'registrar':        'registrar:\s*(.+)',
        'creation_date':    'created:\s*(.+)',
        'expiration_date':  'paid-till:\s*(.+)',
        'name_servers':     'nserver:\s*(.+)',
        'status':           'state:\s*(.+)',
        'emails':           WhoisEntry.regex['emails'],
    }
    def __init__(self, domain, text):
        if text.strip() == 'No entries found':
            raise WhoisError(text)
        else:
            super(WhoisRu, self).__init__(domain, text, self.regex)


class WhoisName(WhoisEntry):
    """
    Whois parser for .name domains.
    """
    regex = {
        'domain_name_id':   'Domain Name ID:\s*(.+)',
        'domain_name':      'Domain Name:\s*(.+)',
        'registrar_id':     'Sponsoring Registrar ID:\s*(.+)',
        'registrar':        'Sponsoring Registrar:\s*(.+)',
        'registrant_id':    'Registrant ID:\s*(.+)',
        'admin_id':         'Admin ID:\s*(.+)',
        'technical_id':     'Tech ID:\s*(.+)',
        'billing_id':       'Billing ID:\s*(.+)',
        'creation_date':    'Created On:\s(.+)',
        'expiration_date':  'Expires On:\s*(.+)',
        'updated_date':     'Updated On:\s*(.+)',
        'name_server_ids':  'Name Server ID:\s*(.+)',
        'name_servers':     'Name Server:\s*(.+)',
        'status':           'Domain Status:\s*(.+)',
    }
    def __init__(self, domain, text):
        if 'No match.' in text:
            raise WhoisError(text)
        else:
            super(WhoisName, self).__init__(domain, text, self.regex)


class WhoisUs(WhoisEntry):
    """
    Whois parser for .us domains.
    """
    regex = {
    'domain_name':                    'Domain Name:\s*(.+)',
    'domain__id':                     'Domain ID:\s*(.+)',
    'registrar':                      'Sponsoring Registrar:\s*(.+)',
    'registrar_id':                   'Sponsoring Registrar IANA ID:\s*(.+)',
    'registrar_url':                  'Registrar URL \(registration services\):\s*(.+)',
    'status':                         'Domain Status:\s*(.+)',
    'registrant_id':                  'Registrant ID:\s*(.+)',
    'registrant_name':                'Registrant Name:\s*(.+)',
    'registrant_address1':            'Registrant Address1:\s*(.+)',
    'registrant_address2':            'Registrant Address2:\s*(.+)',
    'registrant_city':                'Registrant City:\s*(.+)',
    'registrant_state_province':      'Registrant State/Province:\s*(.+)',
    'registrant_postal_code':         'Registrant Postal Code:\s*(.+)',
    'registrant_country':             'Registrant Country:\s*(.+)',
    'registrant_country_code':        'Registrant Country Code:\s*(.+)',
    'registrant_phone_number':        'Registrant Phone Number:\s*(.+)',
    'registrant_email':               'Registrant Email:\s*(.+)',
    'registrant_application_purpose': 'Registrant Application Purpose:\s*(.+)',
    'registrant_nexus_category':      'Registrant Nexus Category:\s*(.+)',
    'admin_id':                       'Administrative Contact ID:\s*(.+)',
    'admin_name':                     'Administrative Contact Name:\s*(.+)',
    'admin_address1':                 'Administrative Contact Address1:\s*(.+)',
    'admin_address2':                 'Administrative Contact Address2:\s*(.+)',
    'admin_city':                     'Administrative Contact City:\s*(.+)',
    'admin_state_province':           'Administrative Contact State/Province:\s*(.+)',
    'admin_postal_code':              'Administrative Contact Postal Code:\s*(.+)',
    'admin_country':                  'Administrative Contact Country:\s*(.+)',
    'admin_country_code':             'Administrative Contact Country Code:\s*(.+)',
    'admin_phone_number':             'Administrative Contact Phone Number:\s*(.+)',
    'admin_email':                    'Administrative Contact Email:\s*(.+)',
    'admin_application_purpose':      'Administrative Application Purpose:\s*(.+)',
    'admin_nexus_category':           'Administrative Nexus Category:\s*(.+)',
    'billing_id':                     'Billing Contact ID:\s*(.+)',
    'billing_name':                   'Billing Contact Name:\s*(.+)',
    'billing_address1':               'Billing Contact Address1:\s*(.+)',
    'billing_address2':               'Billing Contact Address2:\s*(.+)',
    'billing_city':                   'Billing Contact City:\s*(.+)',
    'billing_state_province':         'Billing Contact State/Province:\s*(.+)',
    'billing_postal_code':            'Billing Contact Postal Code:\s*(.+)',
    'billing_country':                'Billing Contact Country:\s*(.+)',
    'billing_country_code':           'Billing Contact Country Code:\s*(.+)',
    'billing_phone_number':           'Billing Contact Phone Number:\s*(.+)',
    'billing_email':                  'Billing Contact Email:\s*(.+)',
    'billing_application_purpose':    'Billing Application Purpose:\s*(.+)',
    'billing_nexus_category':         'Billing Nexus Category:\s*(.+)',
    'tech_id':                        'Technical Contact ID:\s*(.+)',
    'tech_name':                      'Technical Contact Name:\s*(.+)',
    'tech_address1':                  'Technical Contact Address1:\s*(.+)',
    'tech_address2':                  'Technical Contact Address2:\s*(.+)',
    'tech_city':                      'Technical Contact City:\s*(.+)',
    'tech_state_province':            'Technical Contact State/Province:\s*(.+)',
    'tech_postal_code':               'Technical Contact Postal Code:\s*(.+)',
    'tech_country':                   'Technical Contact Country:\s*(.+)',
    'tech_country_code':              'Technical Contact Country Code:\s*(.+)',
    'tech_phone_number':              'Technical Contact Phone Number:\s*(.+)',
    'tech_email':                     'Technical Contact Email:\s*(.+)',
    'tech_application_purpose':       'Technical Application Purpose:\s*(.+)',
    'tech_nexus_category':            'Technical Nexus Category:\s*(.+)',
    'name_servers':                   'Name Server:\s*(.+)',
    'created_by_registrar':           'Created by Registrar:\s*(.+)',
    'last_updated_by_registrar':      'Last Updated by Registrar:\s*(.+)',
    'creation_date':                  'Domain Registration Date:\s*(.+)',
    'expiration_date':                'Domain Expiration Date:\s*(.+)',
    'updated_date':                   'Domain Last Updated Date:\s*(.+)',
    }
    def __init__(self, domain, text):
        if 'Not found:' in text:
            raise WhoisError(text)
        else:
            super(WhoisUs, self).__init__(domain, text, self.regex)


class WhoisMe(WhoisEntry):
    """
    Whois parser for .me domains.
    """
    regex = {
    'domain_id':                   'Domain ID:(.+)',
    'domain_name':                 'Domain Name:(.+)',
    'creation_date':               'Domain Create Date:(.+)',
    'updated_date':                'Domain Last Updated Date:(.+)',
    'expiration_date':             'Domain Expiration Date:(.+)',
    'transfer_date':               'Last Transferred Date:(.+)',
    'trademark_name':              'Trademark Name:(.+)',
    'trademark_country':           'Trademark Country:(.+)',
    'trademark_number':            'Trademark Number:(.+)',
    'trademark_application_date':  'Date Trademark Applied For:(.+)',
    'trademark_registration_date': 'Date Trademark Registered:(.+)',
    'registrar':                   'Sponsoring Registrar:(.+)',
    'created_by':                  'Created by:(.+)',
    'updated_by':                  'Last Updated by Registrar:(.+)',
    'status':                      'Domain Status:(.+)',
    'registrant_id':               'Registrant ID:(.+)',
    'registrant_name':             'Registrant Name:(.+)',
    'registrant_org':              'Registrant Organization:(.+)',
    'registrant_address':          'Registrant Address:(.+)',
    'registrant_address2':         'Registrant Address2:(.+)',
    'registrant_address3':         'Registrant Address3:(.+)',
    'registrant_city':             'Registrant City:(.+)',
    'registrant_state_province':   'Registrant State/Province:(.+)',
    'registrant_country':          'Registrant Country/Economy:(.+)',
    'registrant_postal_code':      'Registrant Postal Code:(.+)',
    'registrant_phone':            'Registrant Phone:(.+)',
    'registrant_phone_ext':        'Registrant Phone Ext\.:(.+)',
    'registrant_fax':              'Registrant FAX:(.+)',
    'registrant_fax_ext':          'Registrant FAX Ext\.:(.+)',
    'registrant_email':            'Registrant E-mail:(.+)',
    'admin_id':                    'Admin ID:(.+)',
    'admin_name':                  'Admin Name:(.+)',
    'admin_org':                   'Admin Organization:(.+)',
    'admin_address':               'Admin Address:(.+)',
    'admin_address2':              'Admin Address2:(.+)',
    'admin_address3':              'Admin Address3:(.+)',
    'admin_city':                  'Admin City:(.+)',
    'admin_state_province':        'Admin State/Province:(.+)',
    'admin_country':               'Admin Country/Economy:(.+)',
    'admin_postal_code':           'Admin Postal Code:(.+)',
    'admin_phone':                 'Admin Phone:(.+)',
    'admin_phone_ext':             'Admin Phone Ext\.:(.+)',
    'admin_fax':                   'Admin FAX:(.+)',
    'admin_fax_ext':               'Admin FAX Ext\.:(.+)',
    'admin_email':                 'Admin E-mail:(.+)',
    'tech_id':                     'Tech ID:(.+)',
    'tech_name':                   'Tech Name:(.+)',
    'tech_org':                    'Tech Organization:(.+)',
    'tech_address':                'Tech Address:(.+)',
    'tech_address2':               'Tech Address2:(.+)',
    'tech_address3':               'Tech Address3:(.+)',
    'tech_city':                   'Tech City:(.+)',
    'tech_state_province':         'Tech State/Province:(.+)',
    'tech_country':                'Tech Country/Economy:(.+)',
    'tech_postal_code':            'Tech Postal Code:(.+)',
    'tech_phone':                  'Tech Phone:(.+)',
    'tech_phone_ext':              'Tech Phone Ext\.:(.+)',
    'tech_fax':                    'Tech FAX:(.+)',
    'tech_fax_ext':                'Tech FAX Ext\.:(.+)',
    'tech_email':                  'Tech E-mail:(.+)',
    'name_servers':                'Nameservers:(.+)',
    }
    def __init__(self, domain, text):
        if 'NOT FOUND' in text:
            raise WhoisError(text)
        else:
            super(WhoisMe, self).__init__(domain, text, self.regex)


class WhoisFr(WhoisEntry):
    """
    Whois parser for .fr domains.
    """
    regex = {
        'status':           'status:\s*(.+)',
        'registrar':        'registrar:\s*(.+)',
        'anniversary':      'aniversary:\s*(.+)',
        'creation_date':    'created:\s*(.+)',
        'name_servers':     'nserver:\s*(.+)',
        'phone_number':           'phone:\s*(.+)',
        'emails':           WhoisEntry.regex['emails'],
    }
    def __init__(self, domain, text):
        if 'No entries found' in text:
            raise WhoisError(text)
        else:
            super(WhoisFr, self).__init__(domain, text, self.regex)


class WhoisIt(WhoisEntry):
    """
    Whois parser for .it domains.
    """
    #TODO: add regex to parse results
    def __init__(self, domain, text):
        if 'AVAILABLE' in text:
            raise WhoisError("Domain is not registered")
        else:
            super(WhoisIt, self).__init__(domain, text)


class WhoisUk(WhoisEntry):
    """
    Whois parser for .uk domains.
    """
    #TODO: add regex to parse results
    def __init__(self, domain, text):
        if ('No match for' in text) or ('Error for' in text):
            raise WhoisError(text)
        else:
            super(WhoisUk, self).__init__(domain, text)


def cast_date(date_str):
    """
    Convert a date string found in WHOIS to a time object.
    """
    known_formats = [
        '%d-%b-%Y',                 # 02-Jan-2000
        '%Y-%m-%d',                 # 2000-01-02
        '%d-%b-%Y %H:%M:%S %Z',     # 02-Jan-2000 13:30:15 UTC
        '%a %b %d %H:%M:%S %Z %Y',  # Tue Jan 02 13:30:15 GMT 2000
        '%Y-%m-%dT%H:%M:%SZ',       # 2000-01-02T13:30:15Z
    ]
    for format in known_formats:
        try:
            return time.strptime(date_str.strip(), format)
        except ValueError:
            pass
    return None

def extract_domain(url):
    """
    Extract the domain from a given URL.
    >>> extract_domain('http://www.google.com.au/tos.html)
    'google.com.au'
    """
    url = re.sub(r'^.*://', '', url).split('/')[0].lower()
    domain = []
    for section in url.split('.'):
        if section in SUFFIXES:
            domain.append(section)
        else:
            domain = [section]
    return '.'.join(domain)

def whois(url):
    domain = extract_domain(url)
    p = Popen(['whois', domain], stdout=PIPE)
    text = p.stdout.read()
    return WhoisEntry.load(domain, text)

if __name__ == '__main__':
    try:
        url = argv[1]
    except IndexError:
        print 'Usage: %s <url>' % argv[0]
        sysexit(1)
    print whois(url)
