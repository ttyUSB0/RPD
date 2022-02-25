#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 18:32:23 2019
@author: alex

Код для формирования РПД и рейтинг-плана по БД в JSON.
Заполняем файл-основу (LibreOffice *.fodt)
Работа с таблицами:
 Ищем таблицу по имени
 берём последнюю строку, вырезаем её
 вставляем её, заменяя теги.


Вызов из терминала, первый параметр - имя json-файла с данными дисциплины

! ЭУМКД всегда идёт первой в списке доп литературы.

"""

import os
import json
from json.decoder import JSONDecodeError
from bs4 import BeautifulSoup
import copy
import re
from collections import defaultdict
import sys
import subprocess

ClassesNames = {"contact":{
      "lections":'лекции',
      "seminars":'семинары',
      "practical":'практические занятия',
      "workshops":'практикумы',
      "laboratory":'лабораторные работы',
      "colloquiums":'коллоквиумы',
      "design":'курсовое проектирование',
      "consultations":'групповые консультации',
      "individual":'индивидуальная работа с преподавателем',
      "other":'иная контактная внеаудиторная работа'},
    "independent":{
      "theoretical":'изучение обучающимися теоретического курса',
      "tasks":'индивидуальные задания',
      "calculations":'расчетно-графические работы',
      "essay":'эссе',
      "design":'курсовое проектирование',
      "control":'контрольные работы',
      "other":'другие виды самостоятельной работы'}}
# -------------------------- Функции общие ()
def GetJsonFromFile(filePath):
    """ исключает комментарии вида
    ///
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

def isHoursRight(dataJSON):
    """ Проверка часов, суммы должны совпадать
    Проходим по структуре data['Sections'], суммируем часы в счетчики, сверяем с VolumeContact* """
    volume = copy.copy(dataJSON['volume']['contact'])
    volume['theoretical'] = dataJSON['volume']['independent']['theoretical']
    volume['other'] = 0 # Экзамен не учитываем

    for section in dataJSON['sections']:
        for topic in section['topics']:
            volume['lections'] -=  topic['hours']
            if 'laboratory' in topic.keys():
                for lab in topic['laboratory']:
                    volume['laboratory'] -=  lab['hours']
            if 'practical' in topic.keys():
                for pract in topic['practical']:
                    volume['practical'] -=  pract['hours']
            if 'theoretical' in topic.keys():
                volume['theoretical'] -=  topic['theoretical']
    total = 0
    for key in volume.keys():
        if volume[key]!=0:
            print('!!!\t'+key+':'+str(volume[key]))
        total += volume[key]
    if total==0:
        return True
    else:
        return False

def fillContents(Sections):
    """ Заполняем краткое содержание
    Проходим по структуре data['Sections']
    upd 11.2020 Оставил только названия секций"""
    Contents = ''
    for section in Sections:
        Contents += section['name'] #+ ' ('
        #for topic in section['topics']:
        #    Contents += topic['name'][0].lower() + topic['name'][1:] + ', '
        Contents += '; ' #Contents[:-2] + '); '
    return Contents[:-2] + '.'

def FillTags(data):
    """ Создаём словарь с ключами, которые соответствуют ключам в fodt
    Это новый словарь, дополненный. Ключи со сложными значениями, вычисляемые """
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

    dTag['Percent'] = str(int(100*dTag['VolumeIndependentTheoretical']/dTag['VolumeHoursTotal']))

    # оценочные средства ФОС (до перевода Volume в str)
    dTag['fosArsenal'] = ''
    if dTag['VolumeContactPractical']>0:
        dTag['fosArsenal'] += ' вопросы для защиты практических  работ (текущий контроль);'
    if dTag['VolumeContactLaboratory']>0:
        dTag['fosArsenal'] += ' вопросы для защиты лабораторных  работ (текущий контроль);'


    for key in dTag.keys():
        if key.startswith('VolumeContact') or key.startswith('VolumeIndependent'):
            if dTag[key] == 0: # Заменяем нули на минусы
                dTag[key] = '-'
            else:
                dTag[key] = '%.1f(%d)'%(dTag[key]/36, dTag[key])

    # ----- Списки
    # Связана с ...
    dTag['ConnectsWithList']=''
    for item in data['ConnectsWith']:
        dTag['ConnectsWithList']=dTag['ConnectsWithList']+'«'+item+'», '
    dTag['ConnectsWithList'] = dTag['ConnectsWithList'][:-2] + '.'
    # Необходима для ...
    dTag['NecessaryForList']=''
    for item in data['NecessaryFor']:
        dTag['NecessaryForList']=dTag['NecessaryForList']+'«'+item+'», '
    dTag['NecessaryForList'] = dTag['NecessaryForList'][:-2] + ' и др.'

    dTag['Tasks']=''
    for item in data['Tasks']:
        dTag['Tasks']=dTag['Tasks']+' '+item+'; '
    dTag['Tasks'] = dTag['Tasks'][:-2] + '.'

    """ (В зависимости от кода дисциплины в УП выбирается одна из нижеперечисленных формулировок)
    Дисциплина «Наименование дисциплины» (Б1.Б…) входит в обязательную часть блока Б1 «Дисциплины (модули)».
Дисциплина «Наименование дисциплины» (Б1.В…) входит в часть, формируемую участниками образовательных отношений, блока Б1 «Дисциплины (модули)».
Дисциплина «Наименование дисциплины» (Б1.В.ДВ…) входит в часть, формируемую участниками образовательных отношений, блока Б1 «Дисциплины (модули)» и относится к элективным дисциплинам.
Дисциплина «Наименование дисциплины» (Ф…) относится к  факультативным дисциплинам.
Дисциплина «Наименование дисциплины» (ЭД…) относится к элективным дисциплинам по физической культуре и спорту.
    """

    dTag['CodeUp'] = data['CodeUp']
    dTag['PartName'] = 'входит в '
    CodeUp = data['CodeUp'].split('.')

    if CodeUp[0].startswith('Б'):
        if CodeUp[1].startswith('Б'):
            dTag['PartName'] += 'обязательную часть блока Б%s «Дисциплины (модули)»'%(CodeUp[0][1:],)
            dTag['PlaceInStruct'] = 'Дисциплина «%s» (%s) входит в обязательную часть блока Б1 «Дисциплины (модули)».'%(dTag['Name'],dTag['CodeUp'])
        elif CodeUp[1].startswith('В') :
            dTag['PartName'] += 'часть, формируемую участниками образовательных отношений блока Б%s «Дисциплины (модули)»'%(CodeUp[0][1:],)
            dTag['PlaceInStruct'] = 'Дисциплина «%s» (%s) входит в часть, формируемую участниками образовательных отношений, блока Б1 «Дисциплины (модули)».'%(dTag['Name'],dTag['CodeUp'])
            if len(CodeUp) > 2: #    Б1.В.ДВ
                dTag['PartName'] += ' и относится к дисциплинам по выбору студента'
                dTag['PlaceInStruct'] = 'Дисциплина «%s» (%s) входит в часть, формируемую участниками образовательных отношений, блока Б1 «Дисциплины (модули)» и относится к элективным дисциплинам.'%(dTag['Name'],dTag['CodeUp'])

    #code = re.findall(r'[А-Я]+', data['CodeUp'])
    #number = re.findall(r'\d+', data['CodeUp'])

    dTag['Contents'] = fillContents(data['Sections'])
    dTag['competences'] = ', '.join(dataJSON['competences']['items'])

    ClassesSetContact = []
    for key in ClassesNames['contact']:
        if dataJSON['volume']['contact'][key]>0:
            ClassesSetContact.append(key)
    ClassesSetIndependent = []
    for key in ClassesNames['independent']:
        if dataJSON['volume']['independent'][key]>0:
            ClassesSetIndependent.append(key)

    dTag['ClassesSetContact'] = ''
    dTag['ClassesSetContact3pp'] = ''
    dTag['ClassesSetContactPL3pp'] = ''


    if ClassesSetContact: # если непустой список
        if 'lections' in ClassesSetContact:
            dTag['ClassesSetContact'] = 'занятия лекционного типа'
            dTag['ClassesSetContact3pp'] = 'занятия лекционного типа,'
        temp = ClassesSetContact[:]
        temp.remove('lections')
        if temp: # есть что-то кроме lections
            dTag['ClassesSetContact'] += ', занятия семинарского типа ('
            dTag['ClassesSetContact3pp'] += ', занятия семинарского типа '
            for key in temp:
                dTag['ClassesSetContactPL3pp'] += ClassesNames['contact'][key] + ', '
                dTag['ClassesSetContact'] += ClassesNames['contact'][key] + ', '
            dTag['ClassesSetContact'] = dTag['ClassesSetContact'][:-2]
            dTag['ClassesSetContactPL3pp'] = dTag['ClassesSetContactPL3pp'][:-2]
            dTag['ClassesSetContact'] += ')'

    dTag['ClassesSetIndependent'] = ''
    dTag['ClassesDesign'] = ''
    if ClassesSetIndependent: # если непустой список
        for key in ClassesSetIndependent:
            dTag['ClassesSetIndependent'] += ClassesNames['independent'][key] + ', '
        dTag['ClassesSetIndependent'] = dTag['ClassesSetIndependent'][:-2]
        if 'design' in ClassesSetIndependent:
            dTag['ClassesDesign'] = 'Примерный перечень тем курсового проекта приводится в Фонде оценочных средств для проведения текущего контроля и промежуточной аттестации по дисциплине (ФОС), представленном в приложении к рабочей программе.'


    """ Программой дисциплины «Наименование дисциплины» предусмотрены занятия лекционного типа, занятия семинарского типа и самостоятельная работа обучающихся.  (Выбрать необходимый (ые) тип (ы) занятий)
На занятиях семинарского типа выполняются практические работы, лабораторные работы. (Выбрать необходимый (ые) вид (ы) занятий)
Самостоятельная работа предполагает изучение обучающимися теоретического курса, курсовое проектирование, выполнение индивидуальных заданий, выполнение расчетно-графических заданий,  подготовку реферата, написание эссе, выполнение контрольной(ых) работ(ы) по учебной дисциплине, подготовку доклада на семинар, другие виды самостоятельной работы (указать какие). (Выбрать необходимый (ые) вид (ы) занятий)
Примерный перечень тем курсового проекта / работы приводится в Фонде оценочных средств для проведения текущего контроля и промежуточной аттестации по дисциплине (ФОС), представленном в приложении к рабочей программе. (Текст абзаца приводится в случае если выполнение курсового проекта / работы по дисциплине предусмотрено)
Для запланированных видов занятий разработаны учебно-методические материалы, которые включены в состав электронного учебно-методического комплекса дисциплины (ЭУМКД) / дистанционного курса по дисциплине «Наименование дисциплины» [5]. (Указывается ссылка на номер позиции ЭОР - УМК / Дистанционного курса  в п. 7.1. Рекомендуемая  литература РПД)
Практическая подготовка при реализации дисциплины «Наименование дисциплины» организуется путем проведения: отдельных занятий лекционного типа, которые предусматривают передачу обучающимся учебной информации, необходимой для последующего выполнения работ, связанных с будущей профессиональной деятельностью;  практических занятий; практикумов; лабораторных работ, предусматривающих участие обучающихся в выполнении отдельных элементов работ, связанных с будущей профессиональной деятельностью. (Текст абзаца приводится, если по дисциплине, участвующей  в формировании  профессиональной (ых) компетенции (ий), предусмотрены занятия в форме практической подготовки. Нужно указать виды учебной работы, которые реализуются  в форме практической подготовки. Перечень занятий в форме практической подготовки отображается в таблице п. 5.4.)
    """



    return (dTag, ClassesSetContact, ClassesSetIndependent)


# ------------------------------ Функции работы с xml (fodt)
def addFilledRow(table, row, dictionary):
    """ добавление строки, с заменёнными из словаря ключами {}"""
    newRow = copy.copy(row)
    for item in newRow.findAll(text=re.compile('{*\w}')):
        string = item.parent.string
        item.parent.string = string.format(**dictionary)
    table.insert(-1, newRow)

def fillTableCompetences(soup, tableName, competences):
    """ Заполняем таблицу компетенций """
    table = soup.find(name='table:table', attrs={'table:name':tableName})
    if table is None:
        raise NameError(tableName + ' not found!')
    rows = table.findAll(name='table:table-row')
    lastRow = rows[-1]
    for key in competences:
        addFilledRow(table, lastRow, competences[key])
    lastRow.extract()

def fillTableCompetencesControl(soup, Sections, competences, attestation):
    """ Заполняем таблицу контроля компетенций """
    table = soup.find(name='table:table', attrs={'table:name':'tblCompControl'})
    if table is None:
        raise NameError('tblCompControl not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    #
    nSection = 1
    comp = ', '.join(competences) # список компетенций
    for section in Sections:
        s = {'n':str(nSection), 'section':section['name'].upper()}
        addFilledRow(table, groupRow, s)
        nTopic = 1
        for topic in section['topics']:
            control = []
            if 'theoretical' in topic.keys():
                control.append('устный опрос')
            if 'practical' in topic.keys():
                control.append('решение задач на занятиях семинарского типа')
            if 'laboratory' in topic.keys():
                control.append('защита лабораторной работы')
            control = ' ,'.join(control)
            t = {'n':str(nSection)+'.'+str(nTopic), 'lection':topic['name'],
                 'competences':comp, 'control':control, 'controlType':'Текущий контроль'}
            addFilledRow(table, itemRow, t)
            nTopic += 1
        nSection += 1

    control = 'Промежуточная аттестация по дисциплине: вопросы к ' + attestation
    t = {'n':'', 'lection':'Промежуточная аттестация',
         'competences':comp, 'control':control,
         'controlType':'Промежуточная аттестация по дисциплине'}
    addFilledRow(table, itemRow, t)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()


def fillTableLiterature(soup, Base, Additional):
    """ Заполняем таблицу литературы
    Нумерация сквозная
    """
    table = soup.find(name='table:table', attrs={'table:name':'tblLiterature'})
    if table is None:
        raise NameError('tblLiterature not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    # Основная литература
    newRow = copy.copy(groupRow)
    item = newRow.find(text=re.compile('{*\w}'))
    item.parent.string = 'Основная литература'
    table.insert(-1, newRow)
    i = 1
    for n in range(len(Base)):
        book = copy.copy(Base[n])
        book['n'] = str(i)
        i += 1
        addFilledRow(table, itemRow, book)
    # Дополнительная литература
    newRow = copy.copy(groupRow)
    item = newRow.find(text=re.compile('{*\w}'))
    item.parent.string = 'Дополнительная литература'
    table.insert(-1, newRow)
    for n in range(len(Additional)):
        book = copy.copy(Additional[n])
        book['n'] = str(i)
        i += 1
        addFilledRow(table, itemRow, book)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()

def fillTableLections(soup, Sections):
    """ Заполняем таблицу tblLections
    Проходим по структуре data['Sections'] """
    table = soup.find(name='table:table', attrs={'table:name':'tblLections'})
    if table is None:
        raise NameError('tblLections not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    #
    nSection = 1
    for section in Sections:
        s = {'n':str(nSection), 'section':section['name'].upper()}
        addFilledRow(table, groupRow, s)
        nTopic = 1
        for topic in section['topics']:
            t = {'n':str(nSection)+'.'+str(nTopic), 'lection':topic['name'],
                 'content':topic['content']}
            addFilledRow(table, itemRow, t)
            nTopic += 1
        nSection += 1
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()

def fillTableSections(soup, Sections, competences):
    """ Заполняем таблицу tblSections
    Проходим по структуре data['Sections'] """
    table = soup.find(name='table:table', attrs={'table:name':'tblSections'})
    if table is None:
        raise NameError('tblSections not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    #
    nLection = 0
    nSeminar = 0
    nLaboratory = 0
    nIndependent = 0
    nSection = 1
    for section in Sections:
        s = {'n':str(nSection), 'section':section['name'].upper(),
                 'competences': ', '.join(competences)}
        addFilledRow(table, groupRow, s)

        nTopic = 1
        for topic in section['topics']:
            vLection = topic['hours']
            vSeminar = 0
            if 'practical' in topic.keys():
                for item in topic['practical']:
                    vSeminar += item['hours']
            vLaboratory = 0
            if 'laboratory' in topic.keys():
                for item in topic['laboratory']:
                    vLaboratory += item['hours']
            vIndependent = 0
            if 'theoretical' in topic.keys():
                vIndependent += topic['theoretical']
            nLection += vLection
            nSeminar += vSeminar
            nLaboratory += vLaboratory
            nIndependent += vIndependent
            if vSeminar==0:
                vSeminar = '-'
            if vLaboratory==0:
                vLaboratory = '-'
            if vIndependent==0:
                vIndependent = '-'

            t = {'n':str(nSection)+'.'+str(nTopic), 'lection':topic['name'],
                 'vLection':str(vLection), 'vSeminar':str(vSeminar),
                 'vLaboratory':str(vLaboratory), 'vIndependent':str(vIndependent)}
            addFilledRow(table, itemRow, t)
            nTopic += 1
        nSection += 1

    t = {'n':'', 'lection':'Итого в семестр:',
     'vLection':str(nLection), 'vSeminar':str(nSeminar),
     'vLaboratory':str(nLaboratory), 'vIndependent':str(nIndependent)}
    addFilledRow(table, itemRow, t)
    t['lection'] = 'Всего:'
    addFilledRow(table, itemRow, t)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()


def fillTableSeminar(soup, Sections, tableName, seminarType):
    """ Заполняем таблицу tableName = tblLaboratory/tblPractical
    seminarType = laboratory / practical
    """
    table = soup.find(name='table:table', attrs={'table:name':tableName})
    if table is None:
        raise NameError(tableName + ' not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    nSection = 0 # номер порядковый в списке секций
    iSection = 0 # номер порядковый в таблице
    for section in Sections:
        nSection += 1
        if any(seminarType in topic.keys() for topic in section['topics']): # Проверяем, есть ли лабораторки в темах
            iSection += 1
            s = {'n':str(iSection),
                 'section':'Раздел %d. %s'%(nSection, section['name'].upper())}
            addFilledRow(table, groupRow, s)
            i = 0 # номер порядковый в таблице
            for topic in section['topics']: # пробегаем по топикам
                if seminarType in topic.keys():
                    for seminar in topic[seminarType]:
                        i += 1
                        t = {'n':str(iSection)+'.'+str(i),
                             'lection':topic['name'],
                             'seminar':seminar['name']+' ('+str(seminar['hours'])+'ч)',
                             'content':seminar['content']}
                        addFilledRow(table, itemRow, t)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()

def fillTableCPC(soup, Sections):
    """ Заполняем таблицу tblCPC
    """
    table = soup.find(name='table:table', attrs={'table:name':'tblCPC'})
    if table is None:
        raise NameError('tblCPC not found!')
    rows = table.findAll(name='table:table-row')
    groupRow = rows[-2]
    itemRow = rows[-1]
    nSection = 0 # номер порядковый в списке секций
    iSection = 0 # номер порядковый в таблице
    for section in Sections:
        nSection += 1 # в каждом топике должно быть СРС - поле 'theoretical'
        iSection += 1
        s = {'n':str(iSection),
             'section':'Раздел %d. %s'%(nSection, section['name'].upper())}
        addFilledRow(table, groupRow, s)
        i = 0 # номер порядковый в таблице
        for topic in section['topics']: # пробегаем по топикам
            i += 1
            t = {'n':str(iSection)+'.'+str(i), 'lection':topic['name'],
             'content':topic['content'], 'hours':topic['theoretical']}
            addFilledRow(table, itemRow, t)
    # удаляем первые две служебные строки-заготовки
    groupRow.extract()
    itemRow.extract()

def fillTableClasses(soup, classesTypes):
    """ Заполняем таблицу типов занятий """
    table = soup.find(name='table:table', attrs={'table:name':'tblClasses'})
    if table is None:
        raise NameError('tblClasses not found!')
    rows = table.findAll(name='table:table-row')
    lastRow = rows[-1]
    for item in classesTypes:
        t = {'type':item['name'], 'text':item['text']}
        addFilledRow(table, lastRow, t)
    lastRow.extract()

def fillList(soup, listTag, listContent):
    """ Заполнение списка. Ищем по {listTag}, заполняем из listContent"""
    q = soup.find(text=re.compile('{'+listTag+'}'))
    item = q.parent.parent
    List = item.parent
    for question in listContent:
        newItem = copy.copy(item)
        q = newItem.findChildren("text:p" , recursive=True)[0]
        q.string = q.string.format(**{listTag:question})
        List.insert(-1, newItem)
    item.extract()

def fillTableRating(soup, Seminars):
    """ Заполняем таблицу рейтинг-плана """
    step = len(Seminars)//18 # поделим нацело на колво недель, это колво в неделю
    table = soup.find(name='table:table', attrs={'table:name':'tblRating'})
    if table is None:
        raise NameError('tblRating not found!')
    rows = table.findAll(name='table:table-row')
    itemRow = rows[-1]
    i = 0
    week = 1
    for seminar in Seminars:
        item = copy.copy(seminar)
        item['n'] = str(week)
        item['points'] = str(int(25/6/step)) # раскидываем примерно поровну, надо вручную потом поправить
        addFilledRow(table, itemRow, item)
        i += 1
        if i>=step:
            i = 0
            week += 1
    itemRow.extract()

def fillTableThemes(soup, designThemes):
    """ Заполняем таблицу Темы курсового """
    table = soup.find(name='table:table', attrs={'table:name':'tblDesignThemes'})
    if table is None:
        raise NameError('tblClasses not found!')
    rows = table.findAll(name='table:table-row')
    lastRow = rows[-1]

    if designThemes is None:
        designThemes = ['']

    i = 0 # номер порядковый в таблице
    for theme in designThemes:
        i += 1
        addFilledRow(table, lastRow, {'n':str(i), 'theme':theme})
     # удаляем служебные строки-заготовки
    lastRow.extract()


# ------------------------------ Главный код
if __name__ == "__main__":
    if len(sys.argv)!=2:
        print('[!] Скрипт принимает единственный параметр - имя json-файла с данными дисциплины\nНапример: python3 Syllabus.py "СУ ИИ 2019.json"')
        sys.exit()

    fileOutList = [] # список файлов fodt, которые мы сгенерируем
    folder = os.getcwd()
    fileJSON = sys.argv[1]

    # -------- Читаем JSONы
    raw = GetJsonFromFile(os.path.join(folder, fileJSON))
    try:
        dataJSON = json.loads(raw)
    except JSONDecodeError:
        print ('[!] Проверьте json-файл на корректность (www.jsonlint.com)')
        sys.exit()

    # -------- Проверим на часы
    if not isHoursRight(dataJSON):
        print('[!] Часы в плане (volume) не совпадают с суммой по занятиям (sections)')
        sys.exit()
    else:
        print("[*] С часами всё ОК.")

    # Создаём словарь с ключами, которые соответствуют ключам в fodt
    data = iterData(dataJSON)
    # TODO: Убрать структуру data совсем, только dTag
    # делаем копию словаря data, дополняя его вычисляемыми значениями
    (dTag, ClassesSetContact, ClassesSetIndependent) = FillTags(data)


    # --- компетенции считываем
    raw = GetJsonFromFile(os.path.join(folder, dataJSON['competences']['file']))
    dataComp = json.loads(raw)
    competences = {}
    for key in dataJSON['competences']['items']:
        competences[key] = dataComp[key]

    # --- Виды занятий
    raw = GetJsonFromFile(os.path.join(folder, 'Виды занятий.json'))
    dataClasses = json.loads(raw)
    classes = []
    # contact
    for item in ('lections', 'laboratory', 'practical'):
        if dataJSON['volume']['contact'][item]>0:
            classes.append(item)
    # independent
    for item in ('theoretical', 'design', 'tasks', 'other'):
        if dataJSON['volume']['independent'][item]>0:
            classes.append(item)
    # Оставляем только использованные в РПД типы занятий
    classesTypes = []
    for item in dataClasses:
        if item['type'] in classes:
            classesTypes.append(item)

    # переформатируем список литературы: ключи book,link - из базы
    # В основной литературе не более 5 наименований
    # литература не старше 10 лет (можно в доп. литературу), либо приложить протокол НМС о необходимости и актуальности данных изданий
    raw = json.loads(GetJsonFromFile(os.path.join(folder, 'Литература.json')))
    LiteratureSet = {}
    for item in raw:
        LiteratureSet[item['tag']] = {'book':item['book'], 'link':item['link']}

    def formatBooks(tags):
        """ переформатируем список литературы: ключи book,link - из базы """
        Literature = []
        for tag in tags:
            if tag in LiteratureSet.keys():
                Literature.append(LiteratureSet[tag])
            else:
                print("[!] Не найдена книга %s"%(tag,))
        return Literature
    data['LiteratureBase'] = formatBooks(data['LiteratureBase'])
    data['LiteratureAdditional'] = formatBooks(data['LiteratureAdditional'])
    dTag['umkdN'] = len(data['LiteratureBase']) + 1 #! ЭУМКД всегда идёт первой в списке доп литературы.

    # --------------- РАБОТА С ШАБЛОНОМ
    # -------- Читаем шаблон fodt, заменяем теги
    print('[*] стандарт %s'%(data['StandardName'],))
    if data['StandardName']=="ФГОС ВО":
        fileIn = 'layout.fodt'
        dTag['designThemes'] = None # не знаю, у меня не было КП в этом ФГОС. В шаблоне этого нет
    elif data['StandardName']=="ФГОС 3++":
        fileIn = 'layout3pp.fodt'
    fileOut = (dTag['ProgramCode'] + '_' + dataJSON['competences']['file'].split(' ')[0]+
        ' - ' + fileJSON.split('.')[0] + '.fodt')

    with open(os.path.join(folder, fileIn), "r") as file:
        soup = BeautifulSoup(file.read(), features="xml")

    # таблицы
    fillTableCompetences(soup, 'tblCompAnn', competences)
    fillTableCompetences(soup, 'tblCompMain', competences)
    fillTableCompetences(soup, 'tblCompFOS', competences)
    fillTableCompetencesControl(soup, data['Sections'], dataJSON['competences']['items'], data['VolumeAttestation'])

    fillTableLiterature(soup, data['LiteratureBase'], data['LiteratureAdditional'])
    fillTableLections(soup, data['Sections'])
    fillTableSections(soup, data['Sections'], dataJSON['competences']['items'])
    fillTableSeminar(soup, data['Sections'], 'tblLaboratory', 'laboratory')
    fillTableSeminar(soup, data['Sections'], 'tblPractical', 'practical')

    fillTableClasses(soup, classesTypes)
    fillList(soup, 'tasks', dataJSON['tasks']) # список задач, их два , вызывает два раза
    fillList(soup, 'tasks', dataJSON['tasks'])
    try:
        fillTableThemes(soup, dataJSON['designThemes'])
    except Exception:
        pass
    fillList(soup, 'q', dataJSON['questions']) # список вопросов

    # Заменяем теги значениями из словаря dTag
    for item in soup.findAll(text=re.compile('{*\w}')):
        string = item.parent.string
        if not string is None:
            item.parent.string = string.format(**dTag)
        else:
            item.string = item.string.format(**dTag)

    with open(os.path.join(folder, fileOut), "w") as file:
        file.write(str(soup))
    fileOutList.append(fileOut)
    print('[*] РПД готова!')


    # -------- CPC
    dTag['Seminar'] = ''
    if 'laboratory' in ClassesSetContact:
        dTag['Seminar'] += """ Для успешного выполнения и защиты лабораторной работы
        предварительно необходимо изучить теоретический материал по соответствующей теме,
        методические указания, подготовить отчет по установленной форме. После проведения
        исследований и окончательного оформления отчета проводится защита лабораторной работы.
        """
    if 'practical' in ClassesSetContact:
        dTag['Seminar'] += """ Самостоятельная работа студентов на практических занятиях
        может предусматривать выполнение контрольных работ; решение задач; работу со
        справочной, нормативной документацией и научной литературой; защиту выполненных
        работ; тестирование и т.д. Контроль работы студентов на практических занятиях
        осуществляет преподаватель в соответствии с требованиями рабочей программы
        дисциплины.
        """
    fileIn = 'layCPC.fodt'
    fileOut = (dTag['ProgramCode'] + '_' + dataJSON['competences']['file'].split(' ')[0]+
        ' - ' + fileJSON.split('.')[0] + ' - МУ по СРС.fodt')

    with open(os.path.join(folder, fileIn), "r") as file:
        soup = BeautifulSoup(file.read(), features="xml")

    # таблицы
    fillTableClasses(soup, classesTypes)
    fillTableLiterature(soup, data['LiteratureBase'], data['LiteratureAdditional'])
    fillTableCPC(soup, data['Sections'])

    fillList(soup, 'tasks', dataJSON['tasks']) # список задач

    # Заменяем теги значениями из словаря dTag
    for item in soup.findAll(text=re.compile('{*\w}')):
        string = item.parent.string
        if not string is None:
            item.parent.string = string.format(**dTag)
        else:
            item.string = item.string.format(**dTag)

    with open(os.path.join(folder, fileOut), "w") as file:
        file.write(str(soup))
    fileOutList.append(fileOut)
    print('[*] МУ по СРС готовы!')
    # Sections = data['Sections']

    # -------- Рейтинг-план
    # делим уч. план на занятия: Считаем
    Seminars = []
    hoursList = defaultdict(int)
    for section in data['Sections']:
        for topic in section['topics']: # пробегаем по топикам
            Seminars.append({'type':'Лекция (%dч)'%(topic['hours'],),
                             'content':topic['content'], 'control':'Опрос'})
            hoursList['lections'] += topic['hours']
            if 'laboratory' in topic.keys():
                for work in topic['laboratory']:
                    Seminars.append({'type':'Лабораторная работа (%dч)'%(work['hours'],),
                             'content':work['content'], 'control':'Выполнение и защита отчета'})
                    hoursList['laboratory'] += work['hours']
            if 'practical' in topic.keys():
                for work in topic['practical']:
                    Seminars.append({'type':'Практическое занятие (%dч)'%(work['hours'],),
                             'content':work['content'], 'control':'Выполнение и сдача задания'})
                    hoursList['practical'] += work['hours']
    if len(Seminars)%9 > 0:
            print('[!] Колво занятий не соответствует колву недель')
            sys.exit()


    hours = []
    for (key,value) in hoursList.items():
        hours.append('%d\t-%s'%(value, ClassesNames["contact"][key]))

    # список с типами контроля
    mark = []
    if 'lections' in hoursList.keys():
        mark.append({'type':'Опрос', 'points':str(int(25/6/(len(Seminars)//18)))})
    if 'laboratory' in hoursList.keys():
        mark.append({'type':'Выполнение и защита отчета', 'points':str(int(25/6/(len(Seminars)//18)))})
    if 'practical' in hoursList.keys():
        mark.append({'type':'Выполнение и защита задания', 'points':str(int(25/6/(len(Seminars)//18)))})
    if dataJSON['volume']['attestation'].startswith('зач'):
        mark.append({'type':dataJSON['volume']['attestation'], 'points':'25'})

    dTag['Group'] = ''
    fileIn = 'layRating.fodt'
    fileOut = (dTag['ProgramCode'] + '_' +
        dataJSON['competences']['file'].split(' ')[0]+
        ' - ' + fileJSON.split('.')[0] + ' - Рейтинг-план.fodt')

    with open(os.path.join(folder, fileIn), "r") as file:
        soup = BeautifulSoup(file.read(), features="xml")

    # таблицы
    fillTableRating(soup, Seminars)
    # tblControlType
    table = soup.find(name='table:table', attrs={'table:name':'tblControlType'})
    rows = table.findAll(name='table:table-row')
    itemRow = rows[-1]
    for m in mark:
        addFilledRow(table, itemRow, m)
    itemRow.extract()

    fillList(soup, 'Hours', hours) # список часов

    # Заменяем теги значениями из словаря dTag
    for item in soup.findAll(text=re.compile('{*\w}')):
        string = item.parent.string
        if not string is None:
            item.parent.string = string.format(**dTag)
        else:
            item.string = item.string.format(**dTag)

    with open(os.path.join(folder, fileOut), "w") as file:
        file.write(str(soup))
    fileOutList.append(fileOut)
    print('[*] Рейтинг-план готов!')

    print('[*] Все fodt готовы!')

    for fileOut in fileOutList:
        result = subprocess.run(['loffice', '--convert-to', 'doc', fileOut],
                cwd=folder, capture_output=True, encoding='utf8')
        os.remove(os.path.join(folder, fileOut))
        print(result)
    print('[*] Формирование документов doc завершено успешно! .fodt удалены..')
    print('[-] Удалить лишние таблицы (5.3), обновить содержание.')
    """
    fileOut = fileOutList[0]
    result = subprocess.run(['loffice', '--convert-to', 'pdf', fileOut],
                cwd=folder, capture_output=True, encoding='utf8')
    print(result)
    print('[*] Формирование документов pdf завершено успешно!')
    """

else:
    print('Вызывать из терминала!')