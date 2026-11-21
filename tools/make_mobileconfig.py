#!/usr/bin/env python3
"""Generate naojiat.mobileconfig (iOS web clip profile) for the online site and validate it.

PayloadVersion is the payload *format* version and must be the integer 1 on every payload. It is NOT a
revision counter (setting it to 2 makes iOS refuse the profile with 「不支援承載資料版本」).
To make iOS treat a new build as a fresh profile, change the UUIDs in tools/mobileconfig_ids.json instead.
Usage: python3 tools/make_mobileconfig.py   (writes ./naojiat.mobileconfig, unsigned XML plist, UTF-8, no BOM)
"""
import json, os, plistlib, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
URL = 'https://oopop.okdolle.com/?src=clip'
ROOT_ID = 'io.github.v29sbvpvy2-code.naojiat'
ids = json.load(open(os.path.join(HERE, 'mobileconfig_ids.json')))
icon = open(os.path.join(ROOT, 'icons/icon-180.png'), 'rb').read()

clip = {
  'PayloadType': 'com.apple.webClip.managed', 'PayloadVersion': 1,
  'PayloadIdentifier': ROOT_ID + '.webclip', 'PayloadUUID': ids['webclip'],
  'PayloadDisplayName': '鬧熱牌局', 'PayloadDescription': '在主畫面加入「鬧熱牌局」全螢幕捷徑',
  'URL': URL, 'Label': '鬧熱牌局', 'Icon': icon,
  'IsRemovable': True, 'FullScreen': True, 'Precomposed': True,
}
prof = {
  'PayloadType': 'Configuration', 'PayloadVersion': 1,
  'PayloadIdentifier': ROOT_ID, 'PayloadUUID': ids['profile'],
  'PayloadDisplayName': '鬧熱牌局', 'PayloadOrganization': '鬧熱牌局',
  'PayloadDescription': '安裝後會在主畫面加入「鬧熱牌局」圖示，點開即可全螢幕遊玩台灣麻將、大老二等牌局。此描述檔只加入網頁捷徑，不會安裝程式，也不會管理或讀取你的裝置資料；隨時可在「設定 → 一般 → VPN 與裝置管理」移除。',
  'PayloadRemovalDisallowed': False, 'PayloadScope': 'User',
  'PayloadContent': [clip],
}

# ---- validation (keys/types per Apple's Configuration Profile Reference / ProfileManifests) ----
UUID = re.compile(r'^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$')
COMMON = {'PayloadType': str, 'PayloadVersion': int, 'PayloadIdentifier': str, 'PayloadUUID': str, 'PayloadDisplayName': str, 'PayloadDescription': str, 'PayloadOrganization': str}
TOP = dict(COMMON, PayloadContent=list, PayloadRemovalDisallowed=bool, PayloadScope=str)
CLIP = dict(COMMON, URL=str, Label=str, Icon=bytes, IsRemovable=bool, FullScreen=bool, Precomposed=bool)
REQ = ['PayloadType', 'PayloadVersion', 'PayloadIdentifier', 'PayloadUUID', 'PayloadDisplayName']
def check(p, allowed, kind):
    for k in REQ: assert k in p, f'{kind}: missing {k}'
    for k, v in p.items():
        assert k in allowed, f'{kind}: unknown key {k}'
        t = allowed[k]; assert type(v) is t, f'{kind}: {k} must be {t.__name__}, got {type(v).__name__}'
    assert p['PayloadVersion'] == 1, f'{kind}: PayloadVersion must be 1'
    assert UUID.match(p['PayloadUUID']), f'{kind}: bad UUID'
def validate(d):
    check(d, TOP, 'profile'); assert d['PayloadType'] == 'Configuration' and d['PayloadScope'] in ('User', 'System')
    assert len(d['PayloadContent']) == 1
    c = d['PayloadContent'][0]; check(c, CLIP, 'webclip'); assert c['PayloadType'] == 'com.apple.webClip.managed'
    for k in ('URL', 'Label', 'Icon', 'IsRemovable', 'FullScreen', 'Precomposed'): assert k in c, 'webclip: missing ' + k
    assert c['URL'].startswith('https://') and c['Icon'][:8] == b'\x89PNG\r\n\x1a\n'
    assert d['PayloadUUID'] != c['PayloadUUID'] and d['PayloadIdentifier'] != c['PayloadIdentifier']

validate(prof)
out = os.path.join(ROOT, 'naojiat.mobileconfig')
with open(out, 'wb') as f: plistlib.dump(prof, f, fmt=plistlib.FMT_XML, sort_keys=True)
raw = open(out, 'rb').read()
assert raw.startswith(b'<?xml version="1.0" encoding="UTF-8"?>') and not raw.startswith(b'\xef\xbb\xbf')
validate(plistlib.loads(raw))
print('ok', out, len(raw), 'bytes', ids)
