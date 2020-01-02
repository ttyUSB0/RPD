#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 18:32:23 2019
@author: alex

Рейтинг-план
"""

import pylatex as pl
import os



filepath='/home/alex/Учебная работа/РПД/БД/'


geometry_options = ['a4paper', "tmargin=2cm", "lmargin=2.5cm", "rmargin=1.5cm", "bmargin=2cm"]


doc = pl.Document(default_filepath=filepath, geometry_options=geometry_options,
               document_options='12pt', fontenc='T2A,T1', lmodern=False, textcomp=False,
               page_numbers=False)

babel = pl.Package('babel',['english','russian'])
doc.packages.append(babel)
doc.packages.append(pl.Package('array'))

# remove top and bottom whitespace of longtable, FlushRight
#https://tex.stackexchange.com/questions/5683/how-to-remove-top-and-bottom-whitespace-of-longtable
#https://tex.stackexchange.com/questions/27696/extra-intervals-before-and-after-flushright-environment
doc.preamble.append(pl.utils.NoEscape(r'\setlength{\LTpre}{0pt}'))
doc.preamble.append(pl.utils.NoEscape(r'\setlength{\LTpost}{0pt}'))
doc.preamble.append(pl.utils.NoEscape(r'\setlength\topsep{0pt}'))

with doc.create(pl.position.Center()):
    doc.append(pl.utils.NoEscape(r'{\large Рейтинг-план}\\'))
    doc.append(pl.utils.NoEscape(r'{\small по дисциплине}\\[1mm]'))
    doc.append(pl.utils.NoEscape(r'\underline{\large История инженерного образования} \\[2mm]'))
    doc.append(pl.utils.NoEscape(r'Группа: {\large БНЛ18-01}, семестр 3'))

doc.append('Общее количество часов аудиторных занятий: 36')
doc.append(pl.basic.NewLine())

with doc.create(pl.Tabular('cl')) as table:
    table.add_row((36, '- лекции'))

with doc.create(pl.position.FlushRight()):
    with doc.create(pl.Tabular('ll')) as table:
        table.add_row(('Лектор:', 'Лобанов Д.К.'))
        table.add_row(('Преподаватель:', 'Лобанов Д.К.'))

with doc.create(pl.LongTable(pl.utils.NoEscape(r"ccm{7.5cm}>{\centering\arraybackslash}m{1.8cm} >{\centering\arraybackslash}m{2.0cm}"))) as data_table:
    data_table.add_hline()
    data_table.add_row(['Неделя','Вид занятий','Содержание занятий','Вид контроля','Макс кол. баллов'])
    data_table.add_hline()
    data_table.end_table_header()

    row = ['1','Лекции 4ч','Начало инженерного образования в России','Опрос','8']
    data_table.add_row(row)
    data_table.add_row(row)
    data_table.add_hline()

with doc.create(pl.position.FlushRight()):
    doc.append('Итого 75 баллов')

doc.append(pl.utils.NoEscape(r'\vspace{5mm}'))

with doc.create(pl.position.Center()):
    doc.append(pl.utils.NoEscape(r'{\large Критерии оценки}\\'))

    with doc.create(pl.Tabular(pl.utils.NoEscape(r'p{12.2cm} >{\centering\arraybackslash}m{3.0cm}'))) as table:
        table.add_hline()
        table.add_row((pl.utils.NoEscape(r'\centering Вид контроля'), 'Баллы'))
        table.add_hline()
        table.add_row(('Опрос', '8-9'))
        table.add_row(('Зачет', '9'))
        table.add_hline()

doc.append(pl.utils.NoEscape(r'\vspace{5mm}'))

with doc.create(pl.Tabular('p{12.0cm} p{5.0cm}')) as table:
    table.add_row(('Доцент кафедры САУ', 'Д.К. Лобанов'))
    table.add_row(('Зав. кафедрой САУ', 'М.В. Лукьяненко'))

doc.generate_tex(filepath=os.path.join(filepath,'rating'))


if __name__ == '__main__':