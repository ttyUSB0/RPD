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
    """ Создаём словарь с ключами, которые соответствуют ключам в fodt
    Если есть списки, их игнорируем - они обрабатываются отдельно как таблицы
    """
    if type(dataJSON)==dict:
        Data = {}
        for (key, value) in dataJSON.items():
            Prefix = keyPrefix+CapFirstLetter(key)
            newDict = iterData(value, keyPrefix=Prefix)
            Data.update(newDict)
    else:
        Data = {keyPrefix:dataJSON}
    return Data

""" ! как поставить в соответствие теги в документе и в json?
Единообразно не получится, т.к. есть табличные данные (list для лекций) и единичные (Name, Year)

Выделить таблицы отдельно? Обрабатывать их каждый своим алгоритмом?
"""

# -------- Читаем JSON
raw = GetJsonFromFile(os.path.join(folder, fileJSON))
dataJSON = json.loads(raw)

dTag = iterData(dataJSON)





# --------------------------------------- РАБОТА С ШАБЛОНОМ
# -------- Читаем шаблон fodt
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'

with open(os.path.join(folder, fileIn), "r") as file:
    # read a list of lines into data
    lines = file.readlines()

for line in lines:
    # Заменяем теги значениями

