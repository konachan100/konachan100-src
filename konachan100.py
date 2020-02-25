import sys
from jinja2 import Environment, FileSystemLoader
import os
import os.path
import json
import codecs

def webread(url, readtimeout=30):
    """read page"""
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
                         ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
    return opener.open(url, None, readtimeout).read()

content_cfg = None
with open("content.json", "r") as op:
    content_cfg = json.loads(op.read())

allow_ratings = content_cfg["allow_ratings"]

print("build targets: ", allow_ratings)

loader = FileSystemLoader('./templates')
env = Environment(loader = loader)
template_pc = env.get_template('postlist.html')
template_mobile = env.get_template('postlist_mobile.html')
template_categoaries = env.get_template('categoary_list.html')

if not os.path.exists('buildcount.txt'):
    with open('buildcount.txt', 'w') as f:
        f.write('0')
buildcount = 0
with open('buildcount.txt', 'r') as f:
    buildcount = int(f.read())
print('Build count: ', buildcount)

class PostList:
    def __init__(self):
        self.url = ''
        self.name = ''
        self.rating = ''
        self.build_path = ''
        self.target = ''
        self.othertargets = []

    def __init__(self, cfg):
        self.url = cfg['url']
        self.name = cfg['name']
        self.rating = cfg['rating']
        self.build_path = cfg['build_path']
        self.target = ''
        self.othertargets = []
    
    def get_data(self):
        try:
            print("Loading URL: "+ self.url)
            result = webread(self.url).decode()
            print("Success, decoding JSON")
            data = json.loads(result)
            return data
        except Exception as e:
            print("Failed, "+str(e))
            return None

    def render_pc(self, post_list):
        if post_list is None:
            return
        row = []
        col = []
        for p in post_list:
            col.append(p)
            if len(col)>=4:
                row.append(col)
                col = []
        if len(col)>0:
            row.append(col)
        output = self.build_path+'index.html'
        print("Rendering to "+output)
        page = template_pc.render(postrow = row, target = self.target, othertargets = self.othertargets)
        with codecs.open(output, 'w', 'utf-8') as fn:
            fn.write(page)
        print("Page refreshed")

    def render_mobile(self, post_list):
        if post_list is None:
            return
        output = self.build_path+'m/index.html'
        print("Rendering to "+output)
        page = template_mobile.render(posts = post_list, target = self.target, othertargets = self.othertargets)
        with codecs.open(output, 'w', 'utf-8') as fn:
            fn.write(page)
        print("Page refreshed")

    def build(self):
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)
        if not os.path.exists(self.build_path+"m/"):
            os.makedirs(self.build_path+"m/")
                    
        data = self.get_data()
        self.render_pc(data)
        self.render_mobile(data)
       


## test

# p = PostList(content_cfg['home'][0])
# p.build()

pl_home = content_cfg['home']
pl_cate = content_cfg['categoaries']

current_build_index = (buildcount%len(pl_home), buildcount%len(pl_cate))
print('Current build: Home[%d], Categoary[%d]'%current_build_index)

if len(pl_home)>0:
    PostList(pl_home[current_build_index[0]]).build()
if len(pl_cate)>0:
    PostList(pl_cate[current_build_index[1]]).build()

with open('buildcount.txt', 'w') as f:
    f.write(str(buildcount+1))

page = template_categoaries.render(categoary_list = pl_cate)
with codecs.open('../c/index.html', 'w', 'utf-8') as fn:
    fn.write(page)