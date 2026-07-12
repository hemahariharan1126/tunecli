import requests, re, json

track_id = '5ChkMS8OtdzJeqyybCc9R5'
embed_url = f'https://open.spotify.com/embed/track/{track_id}'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(embed_url, headers=headers, timeout=10)
print('Status:', r.status_code)

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    try:
        track = data['props']['pageProps']['state']['data']['entity']
        print('Title  :', track.get('name'))
        print('Artists:', [a['name'] for a in track.get('artists', [])])
        print('Duration:', track.get('duration'))
    except KeyError as e:
        print('KeyError:', e)
        print('Keys at props.pageProps:', list(data.get('props', {}).get('pageProps', {}).keys()))
else:
    print('No __NEXT_DATA__ found')
    og_title = re.search(r'<meta property="og:title" content="(.*?)"', r.text)
    og_desc  = re.search(r'<meta property="og:description" content="(.*?)"', r.text)
    print('og:title:', og_title.group(1) if og_title else 'NOT FOUND')
    print('og:desc :', og_desc.group(1) if og_desc else 'NOT FOUND')
    print(r.text[:3000])
