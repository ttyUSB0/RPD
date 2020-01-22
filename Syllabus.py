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
from bs4 import BeautifulSoup

folder='/home/alex/Учебная работа/РПД/БД/'

def GetJsonFromFile(filePath):
    """ исключает комментарии
    //
    /* */
    https://stackoverflow.com/a/57814048/5355749
    """
    contents = ""
    fh = open(filePath)
    for line in fh:
        cleanedLine = line.split("///", 1)[0]
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

 Работа с таблицами:
 Ищем таблицу по имени
 берём последнюю строку, вырезаем её
 вставляем её, заменяя теги.
"""

# -------- Читаем JSONы
fileCompetences = 'ЭККА компетенции.json'
fileJSON = 'НЭ ЭК КА.json'

raw = GetJsonFromFile(os.path.join(folder, fileJSON))
dataJSON = json.loads(raw)

data = iterData(dataJSON)
dTag = {} # Здесь будут только единичные данные (не списки)
for (key, value) in data.items():
    if not(type(value) is list):
        dTag.update({key: value})

# Расчеты часов, к заполнению в поля
dTag['VolumeContactSeminarsTotal'] = (dTag['VolumeContactSeminars']+
    dTag['VolumeContactPractical']+
    dTag['VolumeContactWorkshops']+
    dTag['VolumeContactLaboratory']+
    dTag['VolumeContactColloquiums'])
dTag['VolumeContactAnother'] = (dTag['VolumeContactDesign']+
    dTag['VolumeContactConsultations']+
    dTag['VolumeContactIndividual'])

dTag['VolumeContactTotal'] = (dTag['VolumeContactLections']+
    dTag['VolumeContactSeminarsTotal']+
    dTag['VolumeContactAnother']+
    dTag['VolumeContactOther'])

dTag['VolumeIndependentTotal'] = (dTag['VolumeIndependentTheoretical']+
    dTag['VolumeIndependentTasks']+
    dTag['VolumeIndependentCalculations']+
    dTag['VolumeIndependentEssay']+
    dTag['VolumeIndependentDesign']+
    dTag['VolumeIndependentControl']+
    dTag['VolumeIndependentOther'])

dTag['VolumeHoursTotal'] = (dTag['VolumeContactTotal']+
    dTag['VolumeIndependentTotal'])
dTag['VolumePointsTotal'] = int(dTag['VolumeHoursTotal']/36)

# Заменяем нули на минусы
for (key, value) in dTag.items():
    if key.startswith('Volume') and value==0:
        dTag[key] = '-'

# Списки
dTag['ConnectsWithList']=''
for item in data['ConnectsWith']:
    dTag['ConnectsWithList']=dTag['ConnectsWithList']+'«'+item+'», '
dTag['ConnectsWithList'] = dTag['ConnectsWithList'][:-2] + '.'

dTag['NecessaryForList']=''
for item in data['NecessaryFor']:
    dTag['NecessaryForList']=dTag['NecessaryForList']+'«'+item+'», '
dTag['NecessaryForList'] = dTag['NecessaryForList'][:-2] + ' и др.'

dTag['Tasks']=''
for item in data['Tasks']:
    dTag['Tasks']=dTag['Tasks']+' '+item+'; '
dTag['Tasks'] = dTag['Tasks'][:-2] + '.'

#TODO: спросить расшифровку кода УП, сформировать строку
import re
code = re.findall(r'[А-Я]+', data['CodeUp'])
number = re.findall(r'\d+', data['CodeUp'])

dTag['PartName'] = ''
dTag['Type'] = ''
dTag['Contents'] = ''
dTag['CodeUp'] = ''

# --- компетенции
raw = GetJsonFromFile(os.path.join(folder, fileCompetences))
dataComp = json.loads(raw)
competences = {}
for key in data['Competences']:
    competences[key] = dataComp[key]


def fillTableCompetences(tableName, competences):
    """ Заполняем таблицу компетенций """
    table = soup.find(name='table:table', attrs={'table:name':tableName})
    rows = table.findAll(name='table:table-row')
    lastRow = rows[-1]
    for key in competences:
        newRow = copy.copy(lastRow)
        for item in newRow.findAll(text=re.compile('{*\w}')):
            string = item.parent.string
            item.parent.string = string.format(**competences[key])
        table.insert(-1, newRow)
    lastRow.extract()


def fillTableLiterature(Base, Additional):
    """ Заполняем таблицу литературы """
    table = soup.find(name='table:table', attrs={'table:name':'tblLiterature'})
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    # Основная литература
    newRow = copy.copy(groupRow)
    item = newRow.find(text=re.compile('{*\w}'))
    item.parent.string = 'Основная литература'
    table.insert(-1, newRow)
    for n in range(len(Base)):
        book = copy.copy(Base[n])
        book['n'] = str(n+1)
        newRow = copy.copy(itemRow)
        for item in newRow.findAll(text=re.compile('{*\w}')):
            string = item.parent.string
            item.parent.string = string.format(**book)
        table.insert(-1, newRow)
    # Дополнительная литература
    newRow = copy.copy(groupRow)
    item = newRow.find(text=re.compile('{*\w}'))
    item.parent.string = 'Дополнительная литература'
    table.insert(-1, newRow)
    for n in range(len(Additional)):
        book = copy.copy(Additional[n])
        book['n'] = str(n+1)
        newRow = copy.copy(itemRow)
        for item in newRow.findAll(text=re.compile('{*\w}')):
            string = item.parent.string
            item.parent.string = string.format(**book)
        table.insert(-1, newRow)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()


# --------------------------------------- РАБОТА С ШАБЛОНОМ
# -------- Читаем шаблон fodt, заменяем теги
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'
import copy


with open(os.path.join(folder, fileIn), "r") as file:
    soup = BeautifulSoup(file.read(), features="xml")

# таблицы компетенций
fillTableCompetences('tblCompAnn', competences)
fillTableCompetences('tblCompMain', competences)

fillTableLiterature(data['LiteratureBase'], data['LiteratureAdditional'])


# Заменяем теги значениями из словаря dTag
for item in soup.findAll(text=re.compile('{*\w}')):
    string = item.parent.string
    item.parent.string = string.format(**dTag)

with open(os.path.join(folder, fileOut), "w") as file:
    file.write(str(soup))




