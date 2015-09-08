# -*- coding: utf-8 -*-

# This is taken from:
# https://github.com/unitedstates/congress-legislators/blob/master/scripts/everypolitician.py

import requests
import rtyaml
import scraperwiki
import StringIO

from utils import CURRENT_CONGRESS, states

def yaml_load_from_url(url):
    r = requests.get(url)
    return rtyaml.load(StringIO.StringIO(r.content))

def yaml_load(leafname):
    url_template = 'https://raw.githubusercontent.com/unitedstates/congress-legislators/master/{0}'
    return yaml_load_from_url(url_template.format(leafname))

def value_to_unicode(s):
    if isinstance(s, str):
        return unicode(s, 'utf-8')
    return unicode(s)

def unicode_dict_values(d):
    return {k: value_to_unicode(v) for k, v in d.items()}

def get_chamber(term_type):
    return {
        'rep': 'House of Representatives',
        'sen': 'Senate',
    }[term_type]

def run():
    # Load current legislators.
    data = yaml_load("legislators-current.yaml")
    data_social_media = { }
    for legislator in yaml_load("legislators-social-media.yaml"):
        data_social_media[legislator['id']['bioguide']] = legislator

    # Write out one row per legislator for their current term.
    for legislator in data:
        term = legislator['terms'][-1]

        # TODO: "If someone changed party/faction affilation in the middle of the term, you should include two entries, with the relevant start/end dates set."

        person_data = {
            "id": legislator['id']['bioguide'],
            "name": build_name(legislator, term, 'full'),
            "area": build_area(term),
            "group": term['party'],
            "term": CURRENT_CONGRESS,
            "chamber": get_chamber(term['type']),
            "start_date": term['start'],
            "end_date": term['end'],
            "given_name": legislator['name'].get('first'),
            "family_name": legislator['name'].get('last'),
            "honorific_suffix": legislator['name'].get('suffix'),
            "sort_name": build_name(legislator, term, 'sort'),
            "phone": term.get('phone'),
            "gender": legislator['bio'].get('gender'),
            "birth_date": legislator['bio'].get('birthday'),
            "image": "https://theunitedstates.io/images/congress/original/%s.jpg" % legislator['id']['bioguide'],
            "twitter": data_social_media.get(legislator['id']['bioguide'], {}).get("social", {}).get("twitter"),
            "facebook": data_social_media.get(legislator['id']['bioguide'], {}).get("social", {}).get("facebook"),
            "instagram": data_social_media.get(legislator['id']['bioguide'], {}).get("social", {}).get("instagram"),
            "wikipedia": legislator['id'].get('wikipedia', '').replace(" ", "_"),
            "website": term['url'],
        }
        scraperwiki.sqlite.save(
            unique_keys=['id', 'term', 'chamber', 'start_date'],
            data=unicode_dict_values(person_data)
        )

ordinal_strings = { 1: "st", 2: "nd", 3: "rd", 11: 'th', 12: 'th', 13: 'th' }
def ordinal(num):
    return str(num) + ordinal_strings.get(num % 100, ordinal_strings.get(num % 10, "th"))

def build_area(term):
    # Builds the string for the "area" column, which is a human-readable
    # description of the legislator's state or district.
    ret = states[term['state']]
    if term['type'] == 'rep':
        ret += "’s "
        if term['district'] == 0:
            ret += "At-Large"
        else:
            ret += ordinal(term['district'])
        ret += " Congressional District"
    return ret

def build_name(p, t, mode):
    # Based on:
    # https://github.com/govtrack/govtrack.us-web/blob/master/person/name.py

    # First name.
    firstname = p['name']['first']
    if firstname.endswith('.'):
        firstname = p['name']['middle']
    if p['name'].get('nickname') and len(p['name']['nickname']) < len(firstname):
            firstname = p['name']['nickname']

    # Last name.
    lastname = p['name']['last']
    if p['name'].get('suffix'):
        lastname += ', ' + p['name']['suffix']

    if mode == "full":
        return firstname + ' ' + lastname
    elif mode == "sort":
        return lastname + ', ' + firstname
    else:
        raise ValueError(mode)

if __name__ == '__main__':
  run()
