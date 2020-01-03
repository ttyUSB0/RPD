#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 18:32:23 2019
@author: alex

Код для формирования РПД и рейтинг-плана по БД в JSON.

Заполняем файл-основу (LibreOffice *.fodt)
"""

import os

folder='/home/alex/Учебная работа/РПД/БД/'

fileJSON = 'НЭ ЭК КА.json'
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'

import xml.etree.ElementTree as etree
tree = etree.parse(os.path.join(folder, fileIn))
document = tree.getroot()

body = document.find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}body')
text = body.find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}text')

pColl = text.findall('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p')
for p in pColl:

p = pColl[0]
p.text
# 'МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ'

def printChild(obj):
    print('--- Объект "%s" содержит %d узлов:'%(obj.tag, len(obj)))
    for child in obj:
        print('\t%s'%(child.tag,))






