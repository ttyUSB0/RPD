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

# Таблица компетенций
with open(os.path.join(folder, fileCompetences), "r") as file:
    Competences = json.load(file)
# Компетенции. Ищем строку с {CompetenceTable}, заменяем ее всю на xml-код таблицы
tabCompetencesPrefix = """
   <table:table table:name="TableGoal" table:style-name="TableGoal">
    <table:table-column table:style-name="TableGoal.A"/>
    <table:table-column table:style-name="TableGoal.B"/>
    <table:table-column table:style-name="TableGoal.C"/>
    <table:table-column table:style-name="TableGoal.D"/>
    <table:table-row>
     <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
      <text:p text:style-name="P49">Код компе-тенции</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
      <text:p text:style-name="P49">Содержание компетенции</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
      <text:p text:style-name="P49">Индикаторы достижения компетенции</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.D1" office:value-type="string">
      <text:p text:style-name="P49">Планируемые результаты обучения по дисциплине, соотнесённые с установленными в программе индикаторами достижения компетенции</text:p>
     </table:table-cell>
    </table:table-row>
"""
# Заменяемая часть
tabCompetencesRow = """
    <table:table-row>
     <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
      <text:p text:style-name="P49">{Code}</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
      <text:p text:style-name="P49">{Comp}</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
      <text:p text:style-name="P49">{Indicators}</text:p>
     </table:table-cell>
     <table:table-cell table:style-name="TableGoal.D2" office:value-type="string">
      <text:p text:style-name="P49">{Results}</text:p>
     </table:table-cell>
    </table:table-row>
"""
tabCompetencesSuffix = """
   </table:table>
"""

tabCompetences = tabCompetencesPrefix
for key in data['Competences']:
    comp = Competences[key]
    row = tabCompetencesRow.replace('{Code}', comp['Code'])
    row = row.replace('{Comp}', comp['Comp'])
    row = row.replace('{Indicators}', comp['Indicators'])
    row = row.replace('{Results}', comp['Results'])
    tabCompetences = tabCompetences + row
tabCompetences = tabCompetences + tabCompetencesSuffix


import BeautifulSoup4
text = tabCompetencesPrefix+tabCompetencesRow+tabCompetencesSuffix
with open(os.path.join(folder, 'test.xml'), "w") as file:
    file.write(text)


text = """<?xml version="1.0"?>
<table:table table:name="TableGoal" table:style-name="TableGoal">
<table:table-column table:style-name="TableGoal.A"/>
<table:table-column table:style-name="TableGoal.B"/>
<table:table-column table:style-name="TableGoal.C"/>
<table:table-column table:style-name="TableGoal.D"/>
<table:table-row>
 <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
  <text:p text:style-name="P49">Код компе-тенции</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
  <text:p text:style-name="P49">Содержание компетенции</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.A1" office:value-type="string">
  <text:p text:style-name="P49">Индикаторы достижения компетенции</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.D1" office:value-type="string">
  <text:p text:style-name="P49">Планируемые результаты обучения по дисциплине, соотнесённые с установленными в программе индикаторами достижения компетенции</text:p>
 </table:table-cell>
</table:table-row>
<table:table-row>
 <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
  <text:p text:style-name="P49">{Code}</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
  <text:p text:style-name="P49">{Comp}</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.A2" office:value-type="string">
  <text:p text:style-name="P49">{Indicators}</text:p>
 </table:table-cell>
 <table:table-cell table:style-name="TableGoal.D2" office:value-type="string">
  <text:p text:style-name="P49">{Results}</text:p>
 </table:table-cell>
</table:table-row>
</table:table>"""
root = ET.fromstring(text)







# --------------------------------------- РАБОТА С ШАБЛОНОМ
# -------- Читаем шаблон fodt
fileIn = 'layout.fodt'
fileOut = 'syllabus.fodt'

# Заменяем теги значениями из словаря dTag
with open(os.path.join(folder, fileOut), "w") as fOut:
    with open(os.path.join(folder, fileIn), "r") as fIn:
        for line in fIn: # ситаем построчно входной файл, делае копию строки и работаем с ней
            outLine = line[:]
            if outLine.find('{TableCompetence}')>=0: # таблица, заменяем строку
                outLine = tabCompetences
            else: # не таблица
                for (key, value) in dTag.items():
                    outLine = outLine.replace('{'+key+'}', str(value)) # замена по тегам

            fOut.write(outLine) # построчно пишем в выходной файл







