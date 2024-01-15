import json
import random
import time

import requests
import regex as re
import os
import sys
import matplotlib.pyplot as plt
import networkx as nx
import argparse
from pyvis.network import Network



header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "}
coauthor_pattern = """<a tabindex="-1" href="/citations\?user=(.*?)">(.*?)</a>"""
affiliation_pattern = """class="gsc_prf_ila">(.*?)</a>"""
name_pattern = """<div id="gsc_prf_in">(.*?)</div>"""
research_interest_pattern = """ class="gsc_prf_inta gs_ibl">(.*?)</a>"""
no_link_affiliation_pattern = """<div class="gsc_prf_il">(.*?)</div>"""
citation_pattern = """<td class="gsc_rsb_std">([0-9]*)</td>"""

coauthor_reg = re.compile(coauthor_pattern)
affiliation_reg = re.compile(affiliation_pattern)
name_reg = re.compile(name_pattern)
research_interest_reg = re.compile(research_interest_pattern)
no_link_affiliation_reg = re.compile(no_link_affiliation_pattern)
citation_reg = re.compile(citation_pattern)

session = None
MAX_NAME_LENGTH = 35


# 设置中文显示字体

def get_random_color():
    hex_digits = '0123456789ABCDEF'
    return '#' + ''.join(random.choices(hex_digits, k=6))


def get_author_info(url):  # this function claws the coauthor list from google scholar
    res = {}
    global session
    conn = session.get(url, headers=header)
    while conn.status_code != 200:
        print("response code:" + str(conn.status_code) + " sleep for 2s", flush=True, file=sys.stderr)
        time.sleep(2)
        session = requests.Session()
        conn = session.get(url, headers=header)
    text = conn.content.decode("utf-8")
    aff_text = no_link_affiliation_reg.findall(text)[0]
    if len(aff_text) == 0:
        res["affiliation"] = "Unknown"
    elif len(affiliation_reg.findall(aff_text)) == 0:
        res["affiliation"] = aff_text
    else:
        res["affiliation"] = affiliation_reg.findall(aff_text)[0]
        # res["affiliation"] = affiliation_reg.findall(text)[0]
    coau = coauthor_reg.findall(text)
    res["coauthors"] = []
    for au in coau:
        res["coauthors"].append({"name": au[1] if len(au[1]) < 35 else au[1][:MAX_NAME_LENGTH], "id": au[0]})
    res["name"] = name_reg.findall(text)[0]
    res["name"] = res["name"] if len(res["name"]) < MAX_NAME_LENGTH else res["name"][:MAX_NAME_LENGTH]
    res["research_interest"] = research_interest_reg.findall(text)
    if len(citation_reg.findall(text)) == 0:
        res["citation"] = 1
    else:
        res["citation"] = citation_reg.findall(text)[1]
    return res


def claw_data(root_url, max_depth):
    queue = [(0, root_url)]
    author_info = {}
    tot = 0
    while len(queue) > 0:
        element = queue.pop(0)
        info = get_author_info(element[1])
        tot += 1
        author_info[info["name"]] = info
        if element[0] >= max_depth:
            continue
        for coauthor in info["coauthors"]:
            if coauthor["name"] not in author_info.keys():
                queue.append(
                    (element[0] + 1, "https://scholar.google.com/citations?user=" + coauthor["id"] + "&hl=en&oi=ao"))
    return author_info


def main():
    parser = argparse.ArgumentParser(description="Claw the coauthor network from google scholar")
    parser.add_argument("--url", type=str, help="the url of the root author")
    parser.add_argument("--depth", type=int, default=2, help="the depth of the coauthor network")
    parser.add_argument("--output", type=str, help="the output file name of the image")
    parser.add_argument("--json_output", type=str, default="", help="the output file name of the json")
    parser.add_argument("--size", type=int, default=20, help="the size of the figure")
    parser.add_argument("--proxy", type=str, default="", help="the proxy of the request")
    parser.add_argument("--load_from_json", type=str, default="",
                        help="load the data from json, ignore the url and depth")
    parser.add_argument("--font_size", type=int, default=10, help="label font size of the node")
    parser.add_argument("--line_width", type=int, default=2, help="line width of the edge")
    parser.add_argument("--html_output", type=bool, default=True, help="whether to output html file")
    args = parser.parse_args()
    if args.depth < 0:
        print("Invalid depth")
        return
    if args.depth > 3:
        print("Warning: depth > 3 may cause a great mass to to final image", file=sys.stderr)
    if args.proxy != "":
        os.environ["http_proxy"] = args.proxy
        os.environ["https_proxy"] = args.proxy
    if args.load_from_json == "":
        if requests.get(args.url, headers=header).status_code != 200:
            print("Invalid url")
            return
        global session
        session = requests.Session()
        print("Start clawing data...", flush=True)
        author_info = claw_data(args.url, args.depth)
        print("Clawing finished!", flush=True)
    else:
        with open(args.load_from_json, "r", encoding="utf-8") as f:
            author_info = json.load(f)
        print(f"Loaded from {args.load_from_json}!", flush=True)
    # author_info = claw_data("https://scholar.google.com/citations?user=iHh7IJQAAAAJ&hl=en&oi=ao", 2)
    if args.json_output != "":
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(author_info, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {args.json_output}!", flush=True)
    # setup figure size
    plt.figure(figsize=(args.size, args.size))
    plt.rcParams["font.sans-serif"]=["SimHei"]  # 用来正常显示中文标签
    plt.rcParams["axes.unicode_minus"]=False  # 用来正常显示负号
    G = nx.Graph()
    affiliation_color_list = {}
    node_colors = []
    # generate node info
    for author in author_info.keys():
        research_interest_tag = "\n".join(author_info[author]["research_interest"])
        G.add_node(author,
                   desc=f"""{author_info[author]["name"]}\n{author_info[author]["affiliation"]}\n {research_interest_tag}""")
    # build the graph
    for author in author_info.keys():
        for coauthor in author_info[author]["coauthors"]:
            if coauthor["name"] in author_info.keys():
                G.add_edge(author, coauthor["name"])
    G.remove_nodes_from(list(nx.isolates(G)))  # ignore the nodes that have no edges
    # distribute the color
    for node in G.nodes:
        if author_info[node]["affiliation"] not in affiliation_color_list.keys():
            affiliation_color_list[author_info[node]["affiliation"]] = get_random_color()
    for node in G.nodes:
        node_colors.append(affiliation_color_list[author_info[node]["affiliation"]])
    node_sizes = []
    # size is determined by citation
    for node in G.nodes:
        node_sizes.append(int(author_info[node]["citation"]))
    pos = nx.kamada_kawai_layout(G)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_shape="o", node_color=node_colors, alpha=0.8)
    node_labels = nx.get_node_attributes(G, "desc")
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=args.font_size, font_family="sans-serif")
    nx.draw_networkx_edges(G, pos, width=args.line_width, alpha=0.5)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(args.output)
    print(f"Done! Image saved to {args.output}", flush=True)
    if args.html_output:
        net = Network(f"{args.size * 100}px", f"{args.size * 100}px", notebook=False)
        net.force_atlas_2based()
        net.toggle_physics(True)
        for node in author_info.keys():
            net.add_node(node, value=10 * int(author_info[node]["citation"]),
                         title=author_info[node]["affiliation"] + "\n" + "\n".join(
                             author_info[node]["research_interest"]),
                         group=author_info[node]["affiliation"])
        for edge in G.edges:
            net.add_edge(edge[0], edge[1])

        net.save_graph(args.output.replace(".png", ".html"))
        html_file = args.output.replace(".png", ".html")
        print(f"Html file saved to {html_file}", flush=True)


if __name__ == "__main__":
    main()
