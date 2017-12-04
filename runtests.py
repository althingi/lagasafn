#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest

VERBOSE = True


def create_suite():
    loader = unittest.TestLoader()
    suite = loader.discover('test')
    return suite


def run_tests(suite, verb=1):
    runner = unittest.TextTestRunner(verbosity=verb)
    runner.run(suite)


def main():
    suite = create_suite()
    run_tests(suite, 2 if VERBOSE else 1)


if __name__ == '__main__':
    main()
