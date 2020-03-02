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
cfg_host = content_cfg['host']
cfg_home = content_cfg['home']
cfg_cate = content_cfg['categoaries']
cfg_artists = content_cfg['artists']
cfg_loadonce = content_cfg['loadonce']

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
            self.url = cfg['url'].replace('<host>', cfg_host)
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

    def render_pc(self, post_list, audio = None):
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
        page = template_pc.render(postrow = row, target = self.target, othertargets = self.othertargets, audio = audio)
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
            fn.write(json.dumps(post_list, indent = 4))

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
            print("show posts order by score, reverse")
            self.data.sort(key = (lambda d:d['score']), reverse = True)
        else:
            print("show posts order by time, reverse")
            self.data.sort(key = (lambda d:d['created_at']), reverse = True)
        self.rating = {"s":[], "q":[], "e":[]}
        for d in self.data:
            self.rating[d["rating"]].append(d)
        self.overflow = 0
        for r in self.rating:
            of = len(self.rating[r])- 500
            if  of < self.overflow:
                self.overflow = of
        if self.overflow<0:
            self.overflow = 0

class DataDiscard:
    def __init__(self, data, discardtype, overflow, minsize):
        self.data = list(data)
        if discardtype is None or overflow<=0 or minsize>len(data):
            self.cuted = False
            return
        self.cuted = True
        preservesize = len(self.data) - overflow
        if discardtype == "old":
            self.data.sort(key = (lambda d:d['created_at']), reverse = True)
            self.data = self.data[0:preservesize]

class PostCategoary:
    def __init__(self, cfg=None):
        self.url = None
        self.name = None
        self.build_path = None
        self.cache = None
        self.viewtype = None
        self.discardtype = None
        self.audio = None
        self.post_list = []

        #if self.rating == 'all':
        
        if cfg is not None:
            self.load_cfg(cfg)
        #else:
        #    self.post_list = [PostList(cfg)]
    def setup_postlist(self):
        self.post_list = [PostList(), PostList(), PostList()]
        self.post_list[0].build_path = self.build_path
        self.post_list[1].build_path = self.build_path+'q/'
        self.post_list[2].build_path = self.build_path+'e/'

    def load_cfg(self, cfg):
        if 'url' in cfg:
            self.url = cfg['url'].replace('<host>', cfg_host)
        if 'name' in cfg:
            self.name = cfg['name']
        # self.rating = cfg['rating']
        if 'build_path' in cfg:
            self.build_path = cfg['build_path']
            self.setup_postlist()
        if 'cache' in cfg:
            self.usecache = "cache" in cfg
        if "view" in cfg:
            self.viewtype = cfg["view"]
        if "discard" in cfg:
            self.discardtype = cfg["discard"]
        else:
            self.discardtype = 'old'
        if "audio" in cfg:
            self.audio = cfg["audio"]

    # def init_base(self, cfg):
    #     self.url = None
    #     self.name = None
    #     self.build_path = None
    #     self.cache = None
    #     self.viewtype = None
    #     self.discardtype = None
    #     self.audio = None

    #     if 'url' in cfg:
    #         self.url = cfg['url']
    #     if 'name' in cfg:
    #         self.name = cfg['name']
    #     # self.rating = cfg['rating']
    #     if 'build_path' in cfg:
    #         self.build_path = cfg['build_path']
    #     if 'cache' in cfg:
    #         self.usecache = "cache" in cfg
    #     if "view" in cfg:
    #         self.viewtype = cfg["view"]
    #     if "discard" in cfg:
    #         self.discardtype = cfg["discard"]
    #     else:
    #         self.discardtype = 'old'
    #     if "audio" in cfg:
    #         self.audio = cfg["audio"]

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
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)
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
            self.post_list[i].render_pc(dl, self.audio)
            self.post_list[i].render_mobile(dl)
            self.post_list[i].dump_postlist(dl)

class PostCategoaryArtist(PostCategoary):
    def __init__(self, artistname, page=None):
        super().__init__()
        if page:
            self.url = "http://www.konachan.net/post.json?limit=100&tags=%s&page=%d"%(artistname, page)
        else:
            self.url = "http://www.konachan.net/post.json?limit=100&tags=%s"%(artistname,)
        self.build_path = "../c/artist/%s/"%(artistname,)
        self.setup_postlist()
        self.name = "Artist|"+artistname
        # self.discardtype = 'old'
        # self.viewtype = None
        # self.post_list = [PostList(), PostList(), PostList()]
        # self.post_list[0].build_path = self.build_path
        # self.post_list[1].build_path = self.build_path+'q/'
        # self.post_list[2].build_path = self.build_path+'e/'
        # self.audio = None

## test

# p = PostList(content_cfg['home'][0])
# p.build()



categoaries_obj_list = [PostCategoary(c) for c in cfg_cate]
artist_list = [PostCategoaryArtist(c) for c in cfg_artists]
build_list = categoaries_obj_list + artist_list
if buildcount<len(cfg_loadonce):
    build_list = cfg_loadonce
current_build_index = (buildcount%len(cfg_home), buildcount%len(build_list))
print('Current build: Home[%d], Categoary[%d]'%current_build_index)

if len(cfg_home)>0:
    PostList(cfg_home[current_build_index[0]]).build()
if len(build_list)>0:
    build_list[current_build_index[1]].build()

with open('buildcount.txt', 'w') as f:
    f.write(str(buildcount+1))

categoary_indices_namemap = {}
for c in build_list:
    if c.name and  c.name not in build_list:
        categoary_indices_namemap[c.name] = c
page = template_categoaries.render(categoary_indices = categoary_indices_namemap.values())
with codecs.open('../c/index.html', 'w', 'utf-8') as fn:
    fn.write(page)