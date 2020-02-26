import sys
from jinja2 import Environment, FileSystemLoader
import urllib
import urllib.request
import os
import os.path
import json
import codecs

url_read_cache = {}
def webread(url, readtimeout=30):
    """read page"""
    if url in url_read_cache:
        return url_read_cache[url]
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
                         ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
    result = opener.open(url, None, readtimeout).read()
    url_read_cache[url] = result
    return result

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
    # def __init__(self):
    #     self.url = ''
    #     self.name = ''
    #     self.rating = ''
    #     self.build_path = ''
    #     self.target = ''
    #     self.othertargets = []

    def __init__(self, cfg = None):
        if cfg:
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

    def dump_postlist(self, post_list):
        output = self.build_path+'post.json'
        with codecs.open(output, 'w', 'utf-8') as fn:
            fn.write(json.dumps(output, indent = 4))

    def build(self):
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)
        if not os.path.exists(self.build_path+"m/"):
            os.makedirs(self.build_path+"m/")
                    
        data = self.get_data()
        self.render_pc(data)
        self.render_mobile(data)

class DataView:
    def __init__(self, data, viewtype):
        self.data =list(data)
        if viewtype == "hscore":
            self.data.sort(key = (lambda d:d['score']), reverse = True)
        else:
            self.data.sort(key = (lambda d:d['created_at']), reverse = True)
        self.rating = {"s":[], "q":[], "e":[]}
        for d in data:
            self.rating[d["rating"]].append(d)
        self.overflow = 100000000
        for r in self.rating:
            of = len(self.rating[r])- 100
            if of >0 and of < self.overflow:
                self.overflow = of

class DataDiscard:
    def __init__(self, data, discardtype, overflow, minsize):
        self.data = list(data)
        if discardtype is None or overflow + minsize>len(data):
            self.cuted = False
            return
        self.cuted = True
        preservesize = len(self.data) - overflow
        if discardtype == "old":
            self.data.sort(key = (lambda d:d['created_at']), reverse = True)
            self.data = self.data[0:preservesize]

class PostCategoary:
    def __init__(self, cfg):
        self.post_list = []
        self.url = None
        if 'url' in cfg:
            self.url = cfg['url']
        self.name = None
        if 'name' in cfg:
            self.name = cfg['name']
        # self.rating = cfg['rating']
        self.build_path = cfg['build_path']
        self.usecache = "cache" in cfg
        self.viewtype = None
        if "view" in cfg:
            self.viewtype = cfg["view"]
        self.discardtype = None
        if "discard" in cfg:
            self.discardtype = cfg["discard"]

        #if self.rating == 'all':
        self.post_list = [PostList(), PostList(), PostList()]
        self.post_list[0].build_path = self.build_path
        self.post_list[1].build_path = self.build_path+'q/'
        self.post_list[2].build_path = self.build_path+'e/'
        #else:
        #    self.post_list = [PostList(cfg)]

    def get_data(self):
        if self.url is None:
            print("Skip Loading for build path ", self.build_path)
            return []
        try:
            print("Loading URL: "+ self.url)
            result = webread(self.url).decode()
            print("Success, decoding JSON")
            data = json.loads(result)
            return data
        except Exception as e:
            print("Failed, "+str(e))
            return None
    
    def update_cache(self, data, overwrite = False):
        cache_file = self.build_path+"cache.json"
        print('update cache file ', cache_file)
        if not overwrite:
            cached_list = []
            data_dir = {}
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_list = json.loads(f.read())
                for p in data:
                    data_dir[p["id"]] = p
            for cl in cached_list:
                if cl["id"] not in data_dir:
                    data.append(cl)
        with open(cache_file, 'w') as f:
            print('new cache size ', len(data))
            f.write(json.dumps(data, indent = 4))
        return data       

    def build(self):
        data = self.get_data()
        if data is None:
            return
        self.update_cache(data)
        if self.name is None:
            return
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)
        subdirs = ["m/", "q/", "q/m/", "e/", "e/m/"]
        for sd in subdirs:
            if not os.path.exists(self.build_path+sd):
                os.makedirs(self.build_path+sd)
        #data_dict = {"s":[], "q":[], "e":[]}
        data_view = DataView(data, self.viewtype)
        data_discard = DataDiscard(data, self.discardtype, data_view.overflow, 1000)
        if data_discard.cuted:
            self.update_cache(data_discard.data, True)
        # for d in data:
        #     if d['rating'] in data_dict:
        #         data_dict[d['rating']].append(d)
        data_list = [data_view.rating["s"], data_view.rating["q"], data_view.rating["e"]]
        for i in range(min(3, len(self.post_list))):
            dl = data_list[i]
            if len(dl)>100:
                dl = dl[0:100]
            self.post_list[i].render_pc(dl)
            self.post_list[i].render_mobile(dl)
            self.post_list[i].dump_postlist(dl)
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
    PostCategoary(pl_cate[current_build_index[1]]).build()

with open('buildcount.txt', 'w') as f:
    f.write(str(buildcount+1))

page = template_categoaries.render(categoary_list = pl_cate)
with codecs.open('../c/index.html', 'w', 'utf-8') as fn:
    fn.write(page)