# Scholar Spider
Claw co-authorship from google scholar and plot a relation graph.
An online demo is [demo](https://risingentropy.top/project/2024-scholar-spider)
I am recently searching for PhD mentor, so I write this script to plot a relationship figure. Diameter means the citation on google scholar. Here is the result:

![image](https://github.com/RisingEntropy/scholar-spider/assets/69978374/6435fe85-323e-4256-a475-bcbdff54d97c)

# Dependences
Just find a version casually, it seems ok with various versions.
```
json

matplotlib

requests

networkx

pyvis
```
# Usage
A minimial usage can be:
```
python spider.py --url [url_for_root_author] --depth 2 --output output.png --html_output
```

Claw, save to json file, plot and export a html file:
```
python spider.py --url [url_for_root_author] --depth [search_depth] --output [output_filename.png] --json_output [json_path] --size [figure_size] --html_output
```
Load from saved json:
```
python spider.py --load_from_json [your_file_name].json --size [figure_size] --output output.png
```

Note that you may use
```
--proxy [your_proxy_here]
```
to set a proxy if needed.

use
```
--html_output
```
to export a html file. A html file is much better than the simple png image.

