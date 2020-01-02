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

from xml.dom import minidom

dom = minidom.parse(os.path.join(folder, fileIn))
dom.normalize()

doc = dom.getElementsByTagName('office:document')[0]
body = doc.getElementsByTagName('office:body')[0]
text = body.getElementsByTagName('office:text')[0]

attrib = doc.attributes.item(0)
attrib.value

len(text.childNodes)

def printChild(domObj):
    print('--- Объект "%s" имеет %d атрибутов:'%(domObj.nodeName, len(domObj.attributes)))

    for i in range(len(domObj.attributes)):
        print(domObj.attributes.item(i).value)

    print('--- Объект "%s" содержит %d узлов:'%(domObj.nodeName, len(domObj.childNodes)))
    for child in domObj.childNodes:
        print('* узел "%s" содержит %d доч.узлов'%(child.nodeName, len(child.childNodes)))



printChild(text)


collTextP = text.getElementsByTagName("text:p")
len(collTextP)
textP = collTextP[50]

textP.nodeValue


