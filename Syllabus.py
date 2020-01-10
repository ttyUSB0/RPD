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


# --------------------------------------- РАБОТА С ШАБЛОНОМ
# -------- Читаем шаблон fodt, заменяем теги
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'

# Заменяем теги значениями из словаря dTag
with open(os.path.join(folder, fileIn), "r") as file:
    soup = BeautifulSoup(file.read(), features="xml")

for (key, value) in dTag.items():
    ans = soup.find('p', string=key)


with open(os.path.join(folder, fileOut), "w") as fOut:
    with open(os.path.join(folder, fileIn), "r") as fIn:
        for line in fIn: # ситаем построчно входной файл, делае копию строки и работаем с ней
            outLine = line[:]
            for (key, value) in dTag.items():
                outLine = outLine.replace('{'+key+'}', str(value)) # замена по тегам

            fOut.write(outLine) # построчно пишем в выходной файл


# Работа с таблицами

doc = """
<office:body xmlns:office="dfs" xmlns:text="text">
<text:p text:style-name="P18">РАБОЧАЯ ПРОГРАММА ДИСЦИПЛИНЫ </text:p>
<text:p text:style-name="P17"/>
<text:p text:style-name="P20">{Name}</text:p>
<text:p text:style-name="P17"/>
<text:p text:style-name="P17"/>
<text:p text:style-name="P18">Направление подготовки</text:p>
<text:p text:style-name="P20">{ProgramCode} {ProgramDirection}</text:p>
<text:p text:style-name="P18"/>
<text:p text:style-name="P18">Направленность (профиль) образовательной программы</text:p>
<text:p text:style-name="P20">{ProgramProfile}</text:p>
<text:p text:style-name="P18"/>
<text:p text:style-name="P18"/>
<text:p text:style-name="P18">Уровень высшего образования</text:p>
<text:p text:style-name="P20">{ProgramLevel}</text:p>
</office:body>
"""
soup = BeautifulSoup(doc, features="xml")
print(soup.prettify())

for item in soup.findAll(text='{Name}'):
    item.parent.string = '-----------------------------'

print(soup.prettify())




with open(os.path.join(folder, fileIn), "r") as file:
    soup = BeautifulSoup(file.read(), features="xml")

for item in soup.findAll(text='{Name}'):
    item.string.replace_with = 'ASDFGH'


    item.replace_with = 'ASDFGH'

with open(os.path.join(folder, fileOut), "w") as file:
    file.write(str(soup))





row = ans.parent.parent
table = row.parent


import copy
row2 = copy.copy(row)
row.insert_after(row2)

soup_string = str(soup)

print(soup.prettify())

#tabCompetences = tabCompetencesPrefix
#for key in data['Competences']:
#    comp = Competences[key]
#    row = tabCompetencesRow.replace('{Code}', comp['Code'])
#    row = row.replace('{Comp}', comp['Comp'])
#    row = row.replace('{Indicators}', comp['Indicators'])
#    row = row.replace('{Results}', comp['Results'])
#    tabCompetences = tabCompetences + row
#tabCompetences = tabCompetences + tabCompetencesSuffix

with open(os.path.join(folder, fileOut), "w") as file:
    file.write(str(soup))

