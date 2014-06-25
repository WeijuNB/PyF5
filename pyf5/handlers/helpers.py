import os
import re
import time
from pyf5.settings import RELOADER_TAG


HTML_EXTENSIONS = ['.htm', '.html', '.shtml']
CSS_EXTENSIONS = ['.css', '.less']

SPECIAL_EXTENSIONS = HTML_EXTENSIONS + CSS_EXTENSIONS


def bust_cache(m):
    url = m.group(1)
    if '_f5=' in url:
        new_url = re.sub('_f5=[^&$]_', '_f5=' + str(time.time()), url)
    else:
        if '?' in url:
            new_url = url + '&_f5=' + str(time.time())
        else:
            new_url = url + '?_f5=' + str(time.time())

    ret = m.group(0).replace(url, new_url)
    return ret


def process_html(content):
    content = re.sub('''<(?:link[^>]+href)=['"]?([^'"\s]+)['"]?''', bust_cache, content, flags=re.IGNORECASE)
    content = content.replace('</body>', RELOADER_TAG + '\n</body>')

    return content


def process_css(content):
    """
    anti-cache on import, examples:
    @import url("fineprint.css") print;
    @import url("bluish.css") projection, tv;
    @import 'custom.css';
    @import "common.css" screen, projection;
    @import url('landscape.css') screen and (orientation:landscape);
    """
    import_urls = re.findall(r'''@import .*?['"](.*?)['"].*?;''', content)
    for url in import_urls:
        new_url = url + '?_f5=%s' % time.time()
        content = content.replace(url, new_url)

    # todo: cache bust all url('xxx')
    return content


if __name__ == '__main__':
    print process_html('<link href="/sina.css" rel="stylesheet"><script src="a.js">')