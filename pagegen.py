import sys
from jinja2 import Environment, FileSystemLoader
import os
import os.path
from konachan import *
import json
import codecs

option = None
with open("option.json", "r") as op:
    option = json.loads(op.read())

output_pages = ['s', 'q']
if option["output"]:
    output_pages =  option["output"]

print("build targets: ", output_pages)

loader = FileSystemLoader('./templates')
env = Environment(loader = loader)
template_pc = env.get_template('postlist.html')
template_mobile = env.get_template('postlist_mobile.html')

def gen_post_list_page(post_list, template, output, target, othertargets):
    if post_list is None:
        return
    print("Rendering to "+output)
    page = template.render(posts = post_list, target = target, othertargets = othertargets)
    with codecs.open(output, 'w', 'utf-8') as fn:
        fn.write(page)
    print("Page refreshed")

def gen_post_matrix_page(post_list, template, output, target, othertargets):
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
    print("Rendering to "+output)
    page = template.render(postrow = row, target = target, othertargets = othertargets)
    with codecs.open(output, 'w', 'utf-8') as fn:
        fn.write(page)
    print("Page refreshed")

def build_static_page(target, genfunc, postlist, template, outputpath):
    if target in output_pages:
        genfunc(postlist, template, outputpath, target, output_pages)
    else:
        if os.path.exists(outputpath):
            os.remove(outputpath)


def gen_all_post_list_page(pl_s, pl_q, pl_e):
    print("Generating static pages")
    build_static_page("s",gen_post_matrix_page, pl_s, template_pc, "../index.html")
    build_static_page("q",gen_post_matrix_page, pl_q, template_pc, "../q/index.html")
    build_static_page("e",gen_post_matrix_page, pl_e, template_pc, "../e/index.html")
    build_static_page("s",gen_post_list_page, pl_s, template_mobile, "../m/index.html")
    build_static_page("q",gen_post_list_page, pl_q, template_mobile, "../q/m/index.html")
    build_static_page("e",gen_post_list_page, pl_e, template_mobile, "../e/m/index.html")
    # if 's' in output_pages:
    #     gen_post_matrix_page(pl_s, template_pc, "../index.html")
    # if 'q' in output_pages:
    #     gen_post_matrix_page(pl_q, template_pc, "../q/index.html")
    # if 'e' in output_pages:
    #     gen_post_matrix_page(pl_e, template_pc, "../e/index.html")
    # if 'ms' in output_pages:
    #     gen_post_list_page(pl_s, template_mobile, "../m/index.html")
    # if 'mq' in output_pages:
    #     gen_post_list_page(pl_q, template_mobile, "../q/m/index.html")
    # if 'me' in output_pages:
    #     gen_post_list_page(pl_e, template_mobile, "../e/m/index.html")

def gen():
    pl_s = DataSourceS().Get()
    pl_q = DataSourceQ().Get()
    pl_e = DataSourceE().Get()
    gen_all_post_list_page(pl_s, pl_q, pl_e)

def gentest():
    pl = DataSourceTest().Get()
    gen_all_post_list_page(pl, pl, pl)

if __name__ == "__main__":
    isTest = False
    for arg in sys.argv:
        if arg.strip() == '-t':
            isTest = True
            break
    if isTest:
        gentest()
    else:
        gen()

