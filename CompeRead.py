#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 10:30:31 2020
@author: alex

Формирование json  из компетенций
"""
import os
import re


folder='/home/alex/Учебная работа/РПД/БД/'
fileIn = 'ЭККА компетенции.txt'
fileOut = fileIn.split('.')[0] + '.json'

with open(os.path.join(folder, fileIn), "r") as file:
    f = file.read()

z = f.split('$')
z[0]=z[0][1:]

comp = []

i=0

sepList = ['Знать:', 'Уметь:']

for i in range(len(z)/3):
    A = z[i*3]
    B = z[i*3+1]
    C = z[i*3+2]

    code = A.split('.')[0]
    competence = A[len(code)+1:]

    indicators = B
    results = {}
    for sep in sepList:






