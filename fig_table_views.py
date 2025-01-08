import streamlit as st
import pandas as pd
from datetime import datetime

def create_table(table_day_views, max_days, channel):
    text_cols = 4
    sub_tab_final = table_day_views[table_day_views.channel_name==channel].iloc[:, 1:text_cols+max_days]
    sub_tab_final.columns = ["ID поста", "Дата публикации", "Текущие просмотры"] + [f"{i} д" for i in range(1, max_days+1)]


    return sub_tab_final


def styled_df(df):
    def contains_substring(string, substring):
        # Если подстрока найдена в исходной строке, возвращаем True
        if substring in string:
            return True
        # В противном случае возвращаем False
        else:
            return False

    # Определение списков ключевых слов для разных уровней значимости
    keywords_top = ['(100', '(9', '(8']
    keywords_median = ['(7', '(6', '(5', '(4', '(3']
    keywords_bottom = ['(2', '(1']
    
    def style_contains(cell_value):
        # Проверяем, является ли значение строки и содержит ли оно ключевое слово из списка top
        if isinstance(cell_value, str) and any(keyword in cell_value for keyword in keywords_top) \
                and len(cell_value.split(' (')[1].split('.')[0]) > 1:
            return 'color: green'
        
        # Аналогично проверяем для медианных значений
        elif isinstance(cell_value, str) and any(keyword in cell_value for keyword in keywords_median) \
                and len(cell_value.split(' (')[1].split('.')[0]) > 1:
            return 'color: #8B0000'
        
        # И наконец, для bottom значений
        elif isinstance(cell_value, str) and any(keyword in cell_value for keyword in keywords_bottom) \
                and len(cell_value.split(' (')[1].split('.')[0]) > 1:
            return 'color: red'
        
        # Специальный случай для одиночных символов после скобки
        elif isinstance(cell_value, str) and contains_substring(cell_value, ' (') \
                 and len(cell_value.split(' (')[1].split('.')[0]) == 1:
            return 'color: red'
        
        # Для всех остальных случаев оставляем стиль по умолчанию
        else:
            return ''
    
    # Применение функции стилей ко всем ячейкам DataFrame
    styled_df = df.style.map(style_contains)
    
      # Установка стиля для заголовков
    styled_df.set_table_styles([
        {'selector': 'th', 'props': [('color', '#8B0000')]},
         {'selector': 'tr', 'props': [('border-bottom', '0.5px solid gray')]},
    ])
    

    return styled_df
