#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 10:30:31 2020
@author: alex

Формирование json  из компетенций
"""
import os
import json


folder='/home/alex/Учебная работа/РПД/БД/'
fileIn = 'ЭККА компетенции.txt'
fileIn = 'КТОРИИиЭСУ компетенции.txt'
fileOut = fileIn.split('.')[0] + '.json'

with open(os.path.join(folder, fileIn), "r") as file:
    f = file.read()

z = f.split('$')
z[0]=z[0][1:]

Competences = []

for i in range(int(len(z)/3)):
    A = z[i*3]
    B = z[i*3+1]
    C = z[i*3+2]

    code = A.split('.')[0]
    if code=='':
        print('!!!')
    competence = A[len(code)+1:]

    Competences.append({'Code':code, 'Comp':competence, 'Indicators':B, 'Results':C})

# Переделываем в словарь - удобнее искать
NewComp = {}
for c in Competences:
    NewComp[c['Code']] = c

with open(os.path.join(folder, fileOut), "w") as file:
    json.dump(NewComp, file, ensure_ascii=False, indent=2)






