# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 10:10:14 2018

@author: mbuec
"""

def update_all(dict_b):
    dict_b['index'] = 'hello'
    return dict_b

def update_all_2(dict_b):
    dict_b['index'] = 'hello'

class A():
    def __init__(self, dict_a):
        self.params = dict_a

        self.params['bla'] = 3

    def update(self):
        self.params['blubb'] = self.params['zahl'] / 2

if __name__ is '__main__':
    dict_c = dict()
    dict_c['zahl'] = 4
    print('orig')
    print(dict_c)

    a = A(dict_c)
    print('init')
    print(a.params)

    a.update()
    print('update')
    print(a.params)

    update_all_2(a.params)
    print('update all')
    print(a.params)

#    a.params = update_all(a.params)
#    print('update all')
#    print(a.params)
