#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 18:32:23 2019
@author: alex

Код для формирования РПД и рейтинг-плана по БД в JSON.

Заполняем файл-основу (LibreOffice *.fodt)
"""

import os
import json
import xml.etree.ElementTree as etree

folder='/home/alex/Учебная работа/РПД/БД/'

fileJSON = 'НЭ ЭК КА.json'
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'


def GetJsonFromFile(filePath):
    """ исключает комментарии
    //
    /* */
    https://stackoverflow.com/a/57814048/5355749
    """
    contents = ""
    fh = open(filePath)
    for line in fh:
        cleanedLine = line.split("//", 1)[0]
        if len(cleanedLine) > 0 and line.endswith("\n") and "\n" not in cleanedLine:
            cleanedLine += "\n"
        contents += cleanedLine
    fh.close
    while "/*" in contents:
        preComment, postComment = contents.split("/*", 1)
        contents = preComment + postComment.split("*/", 1)[1]
    return contents


raw = GetJsonFromFile(os.path.join(folder, fileJSON))
data = json.loads(raw)



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






