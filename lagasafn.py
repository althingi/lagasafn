#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import codecs
import logging
import os
import string
import StringIO
import zipfile

import requests
import roman
import lxml.etree

DEFAULT_LOGGING_LVL = logging.DEBUG

HTML_FOLDER = 'html/'
MD_FOLDER = 'md/'

PAGE = {
    'index': 'index.html',
    'index2': '0_forsida.html',
    'list_of_chapters': 'kaflar.html',
    'alternative_list_of_chapters': ['lagas.nr.html', 'lagas.nofn.html'],
    'chapters': [
        '01.html', '02.html', '03.html', '04.html', '05.html', '06.html',
        '07.html', '08.html', '09.html', '10.html', '11.html', '12.html',
        '13.html', '14.html', '15.html', '16.html', '17.html', '18.html',
        '19.html', '20.html', '21.html', '22.html', '23.html', '24.html',
        '25.html', '26.html', '27.html', '28.html', '29.html', '30.html',
        '31.html', '32.html', '33.html', '34.html', '35.html', '36.html',
        '37.html', '38.html', '39.html', '40.html', '41.html', '42.html',
        '43.html', '44.html', '45.html', '46.html', '47.html', '48.html'
    ],
    'ignore': [
        '1943117.html', '1963029.html', '1965016.html', '1976094.html',
        '1979013.202.html', '1981075.html', '1984074.html', '1985068.html',
        '1990038.html', '1993043.html', '1993117.html', '1993118.html',
        '1994017.html', '1994082.html', '1994144.html', '1996011.html',
        '1999134.html', '2001012.html', '2001131.html', '2003007.html',
        '2007090.html', '2010006.html', '2011013.html', '2011124.html',
        '2011125.html', '2012086.html', '2012099.html', '2012100.html',
        '2013066.html', '2013071.html', '2017001.html'
    ]
}


def download_and_extract_newest_lagasafn_zip(logger):
    logger.info(u'Downloading newest lagasafn ZIP archive ..')
    zip_file_url = 'https://www.althingi.is/lagasafn/zip/nuna/allt.zip'
    result = requests.get(zip_file_url, stream=True)
    result.raise_for_status()
    zip_archive = zipfile.ZipFile(StringIO.StringIO(result.content))
    zip_archive.extractall(HTML_FOLDER)
    filelist = [f for f in os.listdir(HTML_FOLDER) if f.endswith('.html')]
    for filename in filelist:
        logger.info(u'ZIP: Extracting %s ..', filename)
        html_txt = u''
        filename_pwd = os.path.join(HTML_FOLDER, filename)
        # [althingi.is bad]
        # codec seems to be "Western (Windows 1252)" or cp1252
        with codecs.open(filename_pwd, 'r', 'cp1252') as html_file:
            html_txt = html_file.read()
        # rewrite html charset declaration
        html_txt = html_txt.replace('charset=iso-8859-1', 'charset=utf-8', 1)
        # [althingi.is bad]
        # deny javascript (mainly spy tools like google analytics anyway)
        html_txt = deny_js_scripts(html_txt)
        # rewrite html files in superior utf-8 codec
        with open(filename_pwd, 'w') as html_file:
            html_file.write(html_txt.encode('utf-8'))
    logger.info(u'ZIP: Extraction finished.')


def deny_js_scripts(html_txt):
    return html_txt.replace(
        '<script', '<!-- [deny_js_scripts]\n<script'
    ).replace(
        '</script>', '</script>\n[/deny_js_scripts] -->'
    ).replace(
        '<noscript', '<!-- [deny_js_scripts]\n<noscript'
    ).replace(
        '</noscript>', '</noscript>\n[/deny_js_scripts] -->'
    )


def convert_html_files_to_md_files(logger):
    logger.info(u'Starting conversion of HTML files to MD ..')
    filelist = [f for f in os.listdir(HTML_FOLDER) if f.endswith('.html')]
    filelist.sort()
    for filename in reversed(PAGE['chapters']):
        filelist.remove(filename)
        filelist.insert(0, filename)
    for filename in reversed(PAGE['alternative_list_of_chapters']):
        filelist.remove(filename)
        filelist.insert(0, filename)
    filelist.remove(PAGE['list_of_chapters'])
    filelist.insert(0, PAGE['list_of_chapters'])
    filelist.remove(PAGE['index2'])
    filelist.insert(0, PAGE['index2'])
    filelist.remove(PAGE['index'])
    filelist.insert(0, PAGE['index'])
    data = {'_v': None, 'laws': {}}
    for filename in filelist:
        if filename in PAGE['ignore']:
            continue
        if filename == PAGE['index2']:
            # index duplicate file
            continue
        html_txt = u''
        filename_pwd = os.path.join(HTML_FOLDER, filename)
        with codecs.open(filename_pwd, 'r', 'utf-8') as html_file:
            html_txt = html_file.read()
        # skip revoked laws
        if u'<small><b>Felld úr gildi skv. ' in html_txt:
            continue
        if u'<small>Felld úr gildi skv. ' in html_txt:
            continue
        if u'<small><b>Fellt úr gildi skv. ' in html_txt:
            # [althingi.is bad]
            # sometimes felld úr gildi and sometimes fellt úr gildi ..
            continue
        md_text = parse_html_to_md(logger, filename, html_txt, data)
        if filename == PAGE['index']:
            # index equilavent in markdown is README
            md_filename = 'README.md'
        else:
            md_filename = filename.replace('.html', '.md')
        md_filename_pwd = os.path.join(MD_FOLDER, md_filename)
        with open(md_filename_pwd, 'w') as outfile:
            outfile.write(md_text.encode('utf-8'))
    logger.info(u'File "%s" is a list of chapters page ..', filename)
    logger.info(u'Finished conversion of HTML files to MD.')


def parse_html_to_md(logger, filename, html_txt, data):
    logger.info(u'Parsing "%s" to markdown ..', filename)
    if filename == PAGE['index']:
        md_txt = parse_index_page(logger, filename, html_txt)
    elif filename == PAGE['list_of_chapters']:
        md_txt = parse_list_of_chapters_page(logger, filename, html_txt)
    elif filename in PAGE['alternative_list_of_chapters']:
        md_txt = parse_alt_sorted_list_of_chapters_page(
            logger, filename, html_txt)
    elif filename in PAGE['chapters']:
        md_txt = parse_chapter_page(logger, filename, html_txt, data)
    else:
        # from here we assume we have a law page
        md_txt = parse_law_page(logger, filename, html_txt, data)
    logger.info(u'Finished parsing "%s".', filename)
    return md_txt


def parse_index_page(logger, filename, html_txt):
    logger.info(u'File "%s" is an index page ..', filename)
    dom = lxml.etree.fromstring(html_txt, lxml.etree.HTMLParser())
    md_txt = u''
    title = dom.find('body').find('h1').text
    md_txt += u'# %s\n\n' % (title, )
    li_elements = dom.find('body').find('ul').findall('li')
    for li_element in li_elements:
        a_element = li_element.find('a')
        a_text = a_element.text
        href = a_element.get('href').replace('.html', '.md')
        md_txt += u'* [%s](%s)\n' % (a_text, href)
    return md_txt


def parse_list_of_chapters_page(logger, filename, html_txt):
    logger.info(u'File "%s" is a list of chapters page ..', filename)
    dom = lxml.etree.fromstring(html_txt, lxml.etree.HTMLParser())
    md_txt = u''
    title = dom.find('body').find('h2').text
    md_txt += u'# %s\n\n' % (title, )
    li_elements = dom.find('body').find('ol').findall('li')
    li_number = 1
    for li_element in li_elements:
        a_element = li_element.find('a')
        a_text = a_element.text
        a_href = a_element.get('href').replace('.html', '.md')
        md_txt += u'%s. [%s](%s)\n' % (li_number, a_text, a_href)
        li_number += 1
    return md_txt


def parse_alt_sorted_list_of_chapters_page(logger, filename, html_txt):
    logger.info(
        u'File "%s" is an alt sorted list of chapters page ..', filename)
    dom = lxml.etree.fromstring(html_txt, lxml.etree.HTMLParser())
    md_txt = u''
    h1_element = dom.find('body').find('h1')
    title = ''.join([x for x in h1_element.itertext()])
    md_txt += u'# %s\n\n' % (title, )
    li_elements = dom.find('body').find('ul').findall('li')
    for li_element in li_elements:
        a_element = li_element.find('a')
        a_text = a_element.text
        a_href = a_element.get('href').replace('.html', '.md')
        if filename == 'lagas.nr.html':
            law_name = [x for x in li_element.itertext()][1].strip()
            md_txt += u'* [%s](%s) %s\n' % (a_text, a_href, law_name)
        else:
            law_name = [x for x in li_element.itertext()][0].strip()
            md_txt += u'* %s [%s](%s)\n' % (law_name, a_text, a_href)
    return md_txt


def parse_chapter_page(logger, filename, html_txt, data):
    logger.info(u'File "%s" is a chapter page ..', filename)
    dom = lxml.etree.fromstring(html_txt, lxml.etree.HTMLParser())
    md_txt = u''
    title = dom.find('body').find('h2').text.replace('Kaflar lagasafns: ', '')
    if data['_v'] is None:
        data['_v'] = [x for x in dom.find('body').itertext()][2].strip()
    md_txt += u'# %s\n\n' % (title, )
    law_number = u''
    law_title = u''
    char_to_number_map = {c: str(ord(c) - 96) for c in string.ascii_lowercase}
    tuple_of_txt_containers = (
        str,
        unicode,
        lxml.etree._ElementStringResult,
        lxml.etree._ElementUnicodeResult
    )
    for body_child in dom.find('body').getchildren():
        if body_child.tag in ('h2', 'hr', 'br', 'h4'):
            continue
        elif body_child.tag is lxml.etree.Comment:
            # we don't care about html comments
            continue
        elif body_child.tag == 'h3':
            law_number, law_title = body_child.text.split(' ', 1)
            for key in char_to_number_map:
                law_number = law_number.replace(key, char_to_number_map[key])
            if law_number.endswith('.'):
                law_number = law_number[:-1]
            md_txt += u'## %s %s\n\n' % (law_number, law_title)
        elif body_child.tag == 'ul':
            if law_number == u'':
                # [althingi.is bad]
                # sometimes we have subchapters for a chapter, sometimes not
                # let's create dummy subchapter when absent for consistency
                law_number, law_title = title.split(' ', 1)
                if law_number.endswith('.'):
                    law_number = '%s.1' % (law_number[:-1], )
                md_txt += u'## %s %s\n\n' % (law_number, law_title)
            li_number = 1
            for li_element in body_child.findall('li'):
                li_child_nodes = [x for x in li_element.xpath('child::node()')]
                md_txt += u'* __%s.%s__ ' % (law_number, li_number)
                law_name = u''
                a_text = None
                a_href = None
                law_key = None
                for li_child_node in li_child_nodes:
                    if type(li_child_node) in tuple_of_txt_containers:
                        li_child_tag = None
                        li_child_text = li_child_node.strip()
                    elif type(li_child_node) is lxml.etree._Element:
                        li_child_tag = li_child_node.tag
                        li_child_text = li_child_node.text
                    if li_child_tag == 'a':
                        a_text = li_child_node.text
                for li_child_node in li_child_nodes:
                    if type(li_child_node) in tuple_of_txt_containers:
                        li_child_tag = None
                        li_child_text = li_child_node.strip()
                    elif type(li_child_node) is lxml.etree._Element:
                        li_child_tag = li_child_node.tag
                        li_child_text = li_child_node.text
                    if li_child_tag is None and li_child_text != '':
                        law_name += li_child_text
                        continue
                    elif li_child_tag == 'a' and li_child_text != a_text:
                        law_name += u'[%s](%s)' % (
                            li_child_text,
                            li_child_node.get(
                                'href'
                            ).replace(
                                '.html', '.md'
                            ).replace(
                                '#REF1', ''
                            )
                        )
                        continue
                    elif li_child_tag == 'a' and li_child_text == a_text:
                        a_href = li_child_node.get(
                            'href'
                        ).replace(
                            '.html', '.md'
                        ).replace(
                            'http://www.althingi.is147/', ''
                        )
                        law_key = a_href.replace('.md', '')
                        continue
                md_txt += law_name
                md_txt += u' [%s](%s)\n' % (a_text, a_href)
                if a_text is None or a_href is None:
                    raise Exception('Failed to find link to lawpage.')
                if law_key is None:
                    raise Exception('Failed to find law key.')
                data['laws'][law_key] = {
                    'name': law_name[:-1],
                    'chapter': '%s.%s' % (law_number, li_number),
                    'nr_and_date': a_text
                }
                li_number += 1
            md_txt += u'\n'
            continue
        elif body_child.tag == 'li':
            # [althingi.is bad]
            # breaking html tag rules
            # li elements should be within ol or ul elements
            li_element = body_child
            law_name = li_element.text
            a_element = li_element.find('a')
            a_text = a_element.text
            a_href = a_element.get('href').replace('.html', '.md')
            md_txt += u'* __%s.%s__ %s [%s](%s)\n\n' % (
                law_number, 1, law_name, a_text, a_href
            )
            data['laws'][a_href.replace('.md', '')] = {
                'name': law_name[:-1],
                'chapter': '%s.%s' % (law_number, 1),
                'nr_and_date': a_text
            }
            continue
        else:
            raise Exception('Unexpected element "%s"' % (body_child.tag, ))
    return md_txt


def parse_law_page(logger, filename, html_txt, data):
    logger.info(u'File "%s" is a law page ..', filename)
    # [althingi.is bad] **VERY BAD**
    # law pages are horrendusly badly structured
    # parsing this nonsense might become very pesky, perhaps even impossible
    tuple_of_txt_containers = (
        str,
        unicode,
        lxml.etree._ElementStringResult,
        lxml.etree._ElementUnicodeResult
    )
    char_to_number_map = {c: str(ord(c) - 96) for c in string.ascii_lowercase}

    def subtxt(node):
        # helper function, stringifies children of provided element
        # stackoverflow source: https://stackoverflow.com/a/44918940/2401628
        children_txt = u''
        for child in node.getchildren():
            children_txt += lxml.etree.tostring(child, encoding='unicode')
        return children_txt

    def isRoman(txt):
        # helper function, checks if string contains valid roman number
        # uses pip module roman: https://pypi.python.org/pypi/roman
        try:
            roman.fromRoman(txt)
            return True
        except roman.InvalidRomanNumeralError:
            return False

    dom = lxml.etree.fromstring(html_txt, lxml.etree.HTMLParser())
    md_txt = u''
    law_info = data['laws'][filename.replace('.html', '')]
    md_txt += u'# %s %s\n\n`%s`\n\n_%s_\n\n' % (
        law_info['chapter'],
        law_info['name'],
        law_info['nr_and_date'],
        data['_v']
    )
    body_child_nodes = [x for x in dom.find('body').xpath("child::node()")]
    empty_texts = ('', )
    beyond_header = False
    for i in range(len(body_child_nodes)):
        element_or_str = body_child_nodes[i]
        if type(element_or_str) in tuple_of_txt_containers:
            tag = None
            text = element_or_str.strip()
        elif type(element_or_str) is lxml.etree._Element:
            tag = element_or_str.tag
            text = element_or_str.text
        if not beyond_header:
            if (tag == 'a' and
               subtxt(element_or_str) ==
               u'<i>Ferill m\xe1lsins \xe1 Al\xfeingi.</i>'):
                # [althingi.is bad]
                # outdated url redirect, https redirects to http ffs *barf*
                law_history_url = element_or_str.get('href').replace(
                    'http://www.althingi.is//dba-bin/ferill.pl',
                    (
                        'https://www.althingi.is/thingstorf/'
                        'thingmalalistar-eftir-thingum/ferill/'
                    )
                )
                md_txt += u'[Ferill málsins á Alþingi](%s)\n' % (
                    law_history_url,
                )
            elif (tag == 'a' and
                  subtxt(element_or_str) ==
                  u'<i>Frumvarp til laga.</i>'):
                # [althingi.is bad]
                # why no https?
                law_proposal_pdf_url = element_or_str.get('href').replace(
                    'http://',
                    'https://'
                )
                md_txt += u'[Frumvarp til laga.](%s)\n\n' % (
                    law_proposal_pdf_url,
                )
            elif (tag == 'small' and 'gildi' in subtxt(element_or_str)):
                small_child_nodes = [
                    x for x in element_or_str.xpath("child::node()")
                ]
                for small_child_node in small_child_nodes:
                    if type(small_child_node) in tuple_of_txt_containers:
                        small_tag = None
                        small_text = small_child_node.strip()
                    elif type(small_child_node) is lxml.etree._Element:
                        small_tag = small_child_node.tag
                        small_text = small_child_node.text
                    if small_tag == 'b':
                        md_txt += u'**%s**\n' % (small_text, )
                    elif small_tag == 'em':
                        md_txt += u'%s\n' % (small_text.strip(), )
                    elif small_tag == 'a':
                        law_change_url = '%s%s' % (
                            'https://althingi.is',
                            small_child_node.get('href')
                        )
                        md_txt += u'[%s](%s) ' % (
                            small_child_node.text,
                            law_change_url
                        )
                    elif small_tag is None and 'gildi' in small_text:
                        md_txt += u'%s\n' % (small_text, )
                    elif small_tag == 'br':
                        md_txt += u'\n'
                        beyond_header = True
            continue
        if tag is None and text in empty_texts:
            continue
        elif tag in ('hr', 'br') and text is None:
            continue
        elif tag == 'b' and text is not None and isRoman(text[:-1]):
            chapter_nr = roman.fromRoman(text[:-1])
            if chapter_nr > 1:
                md_txt += u'\n\n'
            md_txt += u'## %s. kafli\n\n' % (chapter_nr, )
            continue
        elif tag == 'b' and text is not None and '. gr.' in text:
            continue
        elif tag == 'span' and element_or_str.get('id') is not None:
            span_id = element_or_str.get('id')
            if ('M' in span_id and 'L' in span_id and element_or_str.text is
               not None):
                span_text = element_or_str.text
                if span_text.endswith('.'):
                    span_text = span_text[:-1]
                span_text = span_text.lower()
                for key in char_to_number_map:
                    span_text = span_text.replace(
                        key,
                        char_to_number_map[key]
                    )
                if '.' in span_text:
                    span_text = span_text.split('.')[-1]
                if span_text == u'\u2014':
                    # www.fileformat.info/info/unicode/char/2014/index.htm
                    continue
                span_text = u'%s' % (span_text, )
                span_text = span_text.replace(
                    '[', ''
                ).replace(
                    ']', ''
                ).replace(
                    '(', ''
                ).replace(
                    ')', ''
                ).replace(
                    u'\u201e', ''
                )
                if span_text in (u'ú', u'þ', u'æ', u'ö', u'–'):
                    continue
                if span_text in (u'\u2026', u'\u201e10', u' ', u''):
                    continue
                span_int = int(span_text)
                if span_int > 1:
                    md_txt += u'\n'
                md_txt += u'%s. ' % (span_int, )
                continue
            else:
                span_id = span_id.lower()
                for key in char_to_number_map:
                    span_id = span_id.replace(key, '')
                clause_nr = int(span_id)
                if clause_nr > 1:
                    md_txt += u'\n\n'
                md_txt += u'### %s. grein\n\n' % (clause_nr, )
                continue
        elif tag == 'img' and element_or_str.get('src') == 'sk.jpg':
            continue
        elif tag is None and text is not None:
            if text == '/':
                continue
            md_txt += text.strip()
            continue
        elif tag == 'img' and element_or_str.get('src') == 'hk.jpg':
            md_txt += u'\n\n'
            continue
        elif tag == 'sup' and text is not None and text.endswith(')'):
            md_txt += u'<sup>%s</sup> ' % (text, )
            continue
        elif (tag == 'i' and ')' in subtxt(element_or_str) and 'L.' in
              subtxt(element_or_str)):
            small_element = element_or_str[0]
            small_element_children = small_element.getchildren()
            for j in range(len(small_element_children)):
                small_element_child = small_element_children[j]
                if small_element_child.tag != 'a':
                    continue
                supnumber = small_element_children[j - 1].text
                linktext = small_element_child.text
                linkurl = small_element_child.get('href')
                if supnumber == '1)':
                    md_txt += u'\n\n> '
                else:
                    md_txt += u' '
                md_txt += u'<sup>%s</sup> [%s](%s)' % (
                    supnumber,
                    linktext,
                    'https://althingi.is%s' % (linkurl, )
                )
            continue
        elif (tag == 'sup' and body_child_nodes[i + 1] == '/' and
              body_child_nodes[i + 2].tag == 'span'):
            md_txt += u'<sup>%s</sup>&frasl;<sub>%s</sub>' % (
                text,
                body_child_nodes[i + 2].text
            )
            continue
        elif tag == 'span' and body_child_nodes[i - 1] == '/':
            continue
        elif tag == 'a' and text == u'\u2026':
            md_txt += u'[%s](%s)' % (
                text,
                'https://www.althingi.is/lagasafn/leidbeiningar/'
            )
            continue
        elif (tag == 'i' and len(element_or_str.getchildren()) == 0 and text is
              not None):
            md_txt += u'_%s_ ' % (text, )
            continue
        elif (tag == 'i' and len(element_or_str.getchildren()) == 0 and text is
              None):
            continue
        elif tag == 'i' and element_or_str[0].getchildren() > 1:
            i_small_child_nodes = [
                x for x in element_or_str[0].xpath("child::node()")
            ]
            add_space = False
            for i_small_child_node in i_small_child_nodes:
                if type(i_small_child_node) in tuple_of_txt_containers:
                    i_small_tag = None
                    i_small_text = i_small_child_node.strip()
                elif type(i_small_child_node) is lxml.etree._Element:
                    i_small_tag = i_small_child_node.tag
                    i_small_text = i_small_child_node.text
                if add_space:
                    md_txt += u' '
                if i_small_tag == 'sup':
                    if i_small_text == '1)':
                        md_txt += u'\n\n> '
                    else:
                        md_txt += u' '
                    md_txt += u'<sup>%s</sup>' % (i_small_text, )
                    add_space = True
                    continue
                elif i_small_tag is None and i_small_text is not None:
                    md_txt += i_small_text
                    continue
                elif (i_small_tag == 'a' and i_small_text is not None and
                      i_small_child_node.get('href') is not None):
                    md_txt += u'[%s](%s)' % (
                        i_small_text,
                        i_small_child_node.get('href').replace('.html', '.md')
                    )
                    continue
            md_txt += u'\n\n'
            continue
        elif (tag == 'b' and
              element_or_str.text == u'\xc1kv\xe6\xf0i um stundarsakir.'):
            md_txt += u'## %s\n\n' % (element_or_str.text, )
            continue
        elif tag == 'img' and element_or_str.get('src') == '/lagas/hk.jpg':
            # [althingi.is bad]
            # image tag, with src whose image is missing
            continue
        elif tag == 'a':
            md_txt += u' [%s](%s) ' % (
                element_or_str.text,
                element_or_str.get('href').replace('.html', '.md')
            )
            continue
    md_txt += u'\n'
    return md_txt


if __name__ == '__main__':
    # TODO: figure out which CLI tools would be nice to have and add them
    parser = argparse.ArgumentParser(u'Al\xfeingi lagasafn CLI')
    parser.add_argument(
        '--foo',
        action='store',
        type=str,
        help='Help text for -foo',
        required=False
    )
    logging.basicConfig(level=DEFAULT_LOGGING_LVL)
    logger = logging.getLogger(__name__)
    logger.info(u'Al\xfeingi lagasafn CLI started ..')
    arguments = parser.parse_args()
    download_and_extract_newest_lagasafn_zip(logger)
    convert_html_files_to_md_files(logger)
