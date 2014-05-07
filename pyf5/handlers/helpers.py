import os
import re
import time
from pyf5.settings import RELOADER_TAG


HTML_EXTENSIONS = ['.htm', '.html', '.shtml']
CSS_EXTENSIONS = ['.css', '.less']

SPECIAL_EXTENSIONS = HTML_EXTENSIONS + CSS_EXTENSIONS


def process_html(content):
    return content.replace('</body>', RELOADER_TAG + '\n</body>')


def process_css(content):
    """
    anti-cache on import, examples:
    @import url("fineprint.css") print;
    @import url("bluish.css") projection, tv;
    @import 'custom.css';
    @import "common.css" screen, projection;
    @import url('landscape.css') screen and (orientation:landscape);
    """
    import_urls = re.findall(r'@import .*?[\'\"](.*?)[\'\"].*?;', content)
    for url in import_urls:
        new_url = url + '?_f5=%s' % time.time()
        content = content.replace(url, new_url)
    return content
