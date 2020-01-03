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

CapFirstLetter = lambda x: x[0].upper() + x[1:]

def iterData(dataJSON, keyPrefix=''):
    """ Создаём словарь (или список) с ключами, которые соответствуют ключам в fodt
    """
    Data = {}
    if type(dataJSON)==dict:
        for (key, value) in dataJSON.items():
            newKey = keyPrefix+CapFirstLetter(key)
            newValue = iterData(value, keyPrefix=newKey)
            Data.update({newKey: newValue})
    elif type(dataJSON)==list:
        for item in dataJSON:
            Data.append(iterData(value, keyPrefix=newKey))
    else:
        Data = dataJSON
    return Data

""" ! как поставить в соответствие теги в документе и в json?
Единообразно не получится, т.к. есть табличные данные (list для лекций) и единичные (Name, Year)

Выделить таблицы отдельно? Обрабатывать их каждый своим алгоритмом?
"""

# -------- Читаем JSON
raw = GetJsonFromFile(os.path.join(folder, fileJSON))
dataJSON = json.loads(raw)

data = iterData(dataJSON)





# --------------------------------------- РАБОТА С ШАБЛОНОМ
def printChild(obj):
    print('--- Объект "%s" содержит %d узлов:'%(obj.tag, len(obj)))
    for child in obj:
        print('\t%s'%(child.tag,))


# -------- Читаем шаблон fodt
fileIn = 'layTest.fodt'
fileOut = 'syllabus.fodt'

tree = etree.parse(os.path.join(folder, fileIn))
document = tree.getroot()
body = document.find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}body')
text = body.find('{urn:oasis:names:tc:opendocument:xmlns:office:1.0}text')

printChild(text)

# 1. находим первую таблицу - это подписи
for i in range(len(text)):
    if text[i].tag.endswith('table'):
        break
# 2. Переводим ее в текст и сохраняем
PersonTable = etree.tostring(text[i], encoding="utf-8").decode('utf-8')

with open(os.path.join(folder, 'PersonTable.xml'), "w") as text_file:
    text_file.write(PersonTable)

# 3. Меняем значения
PersonTable = PersonTable.replace('Table3', 'TableAuthor')
PersonTable = PersonTable.replace('{PersonAuthorDegree}', 'к.т.н.')
PersonTable = PersonTable.replace('{PersonAuthorRank}', 'доцент')
PersonTable = PersonTable.replace('{PersonAuthorPosition}', 'доцент каф. САУ')
PersonTable = PersonTable.replace('{PersonAuthorName}', 'А.Т. Лелеков')

# 4. Парсим в структру и перезаписываем одну из
pTable = etree.fromstring(PersonTable)

text.remove(text[i])
text.insert(i, pTable)
text.insert(5, pTable)
printChild(text)

tree.write(open(os.path.join(folder, 'layNew.fodt'), 'wb'), encoding='utf-8')




remove(subelement)


pColl = text.findall('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p')
for p in pColl:
    if not(p.text is None):
        print(p.text)

p = pColl[0]
p.text
p.attrib

table = text.findall('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table')[0]

len(table)
printChild(table)

cols = table.findall('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-column')
c0 = cols[0]

printChild(cols)

for p in tColl:
    if not(p.text is None):
        print(p.text)


t.text

p.text
p.attrib










