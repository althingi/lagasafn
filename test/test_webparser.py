#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
import difflib
import unittest

from lagasafn import parse_law_page

EXAMPLES_FOLDER = 'test/examples'


def read_example_file(filename):
    filename_location = '%s/%s' % (EXAMPLES_FOLDER, filename)
    with codecs.open(filename_location, encoding='utf-8') as textfile:
        return textfile.read()


def generate_readable_diff_string(str_a, str_b):
    # https://stackoverflow.com/q/46292481/2401628
    return ''.join(
        difflib.unified_diff(
            str_a.splitlines(True),
            str_b.splitlines(True),
            lineterm='\n'
        )
    )


class TestHtmlToMdParser(unittest.TestCase):

    def run_lawpage_html_to_md_parser_check(self, key, data):
        # inputs
        filename = '%s.html' % (key, )
        filename_md = '%s.md' % (key, )
        html_txt = read_example_file(filename)
        expected_md_txt = read_example_file(filename_md)
        # run parser
        md_txt = parse_law_page(filename, html_txt, data)
        # check results, compare with expected
        diff_txt = generate_readable_diff_string(expected_md_txt, md_txt)
        self.assertMultiLineEqual(expected_md_txt, md_txt, msg=diff_txt)

    def test_Law_1_1_1(self):
        key = '1944033'
        data = {
            '_v': u'Íslensk lög 1. nóvember 2017 (útgáfa 147).',
            'laws': {
                key: {
                    'chapter': u'1.1.1',
                    'name': u'Stjórnarskrá lýðveldisins Íslands',
                    'nr_and_date': u'nr. 33 17. júní 1944'
                }
            }
        }
        self.run_lawpage_html_to_md_parser_check(key, data)


if __name__ == '__main__':
    EXAMPLES_FOLDER = 'examples'
    unittest.main()
