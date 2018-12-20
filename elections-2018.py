import re, os, os.path
import time, random
import json

BASEDIR = os.path.dirname(os.path.abspath(__file__))
assert os.path.isdir(BASEDIR)

def main():
    #write_metadata()
    #download_htmls()
    write_dataset()

def write_metadata():
    with open('metadata.json','w') as f:
        f.write(json.dumps(state_codes(), indent=2))


def download_htmls():
    with open('metadata.json') as f:
        states={}
        for x in json.load(f):
            states.setdefault(x['state_code'],[]).append(x['ac_code'])
        for st_code, ac_codes in states.items():
            for ac in ac_codes:
                crawler(st_code, ac)


def write_dataset():
    with open('assembly-elections-2018.json', 'w') as w:
        with open('metadata.json') as f:
            for metadata in json.load(f):
                html_file = os.path.join(BASEDIR, 'data', metadata['state_code'], metadata['ac_code'] + ".html")
                for rec in parse_html(html_file):
                    w.write(json.dumps(rec) + "\n")  # one line per json formatted record


def state_codes():
    states_html = """
    <option value="S26">Chhattisgarh</option>
    <option value="S12">Madhya Pradesh</option>
    <option value="S16">Mizoram</option>
    <option value="S20">Rajasthan</option>
    <option value="S29">Telangana</option>
    """
    re_st = re.compile(r'\<option\s+value=\"([^"]+)\"\>([^<]+)\</option\>')
    states=[]
    for line in filter(lambda x:len(x)>0, map(lambda x: x.strip(), states_html.splitlines())):
        m = re_st.match(line)
        if m is not None:
            state_code = m.group(1).strip()
            state_name = m.group(2).strip()
            state_key = state_name.lower().replace(' ','')
            with open(os.path.join(BASEDIR, 'htmls', state_key + "-ac.html")) as f:
                ac_codes = constituency_codes(f.read())
            for ac_code in ac_codes:
                states.append({'state_code': state_code, 'state_name': state_name, 'ac_name': ac_code['name'], 'ac_code': ac_code['id']})
    return states


def constituency_codes(ac_html):
    ac=[]
    re_ac = re.compile(r'\<option\s+value=\"([^"]+)\"\>([^<]+)\</option\>')
    for line in filter(lambda x:len(x)>0, map(lambda x: x.strip(), ac_html.splitlines())):
        m = re_ac.match(line)
        if m is not None:
            ac.append({'name': m.group(2).strip(), 'id': m.group(1).strip()})
    return ac


def crawler(state_code, ac_code):
    import urllib2
    url = 'http://eciresults.nic.in/Constituencywise{}{}.htm?ac={}'.format(state_code, ac_code, ac_code)

    n = 0
    while n < 2:
        try:
            response = urllib2.urlopen(url, timeout=30)
            content = response.read()
            outdir = os.path.join(BASEDIR, 'data', state_code)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            outpath = os.path.join(outdir, "{}.html".format(ac_code))
            f = open(outpath, 'w')
            f.write(content)
            print "##",outpath
            f.close()
            break
        except urllib2.URLError as e:
            n += 1
            print type(e)


def parse_html(path_to_html):
    from BeautifulSoup import BeautifulSoup
    parsed = []
    st = os.path.basename(os.path.dirname(path_to_html))
    ac = os.path.splitext(os.path.basename(path_to_html))[0]
    with open(path_to_html) as f:
        html = BeautifulSoup(f.read())
        div = html.findAll('div', id='div1')
        assert len(div) == 1
        for tr in div[0].table.findAll('tr'):
            tds = tr.findAll('td')
            if len(tds) == 3:
                parsed.append({ 'state': st,
                                'ac'   : ac,
                                'name' : tds[0].string,
                                'party': tds[1].string,
                                'votes': int(tds[2].string)})
    return parsed


###################################
if __name__ == "__main__":
    main()
###################################
