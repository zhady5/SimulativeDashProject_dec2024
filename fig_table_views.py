import streamlit as st
import pandas as pd
from datetime import datetime

def create_table(post_view, max_days, channel):
    filtered_post_view = post_view[(post_view['days_diff'] <= max_days) & (post_view.channel_name == channel)].copy()
    filtered_post_view = filtered_post_view.groupby(['post_datetime', 'post_id', 'current_views', 'days_diff'])[['view_change', 'percent_new_views']].sum().reset_index()
    grouped_df = filtered_post_view.groupby(['post_datetime', 'post_id']).agg({
        'view_change': lambda x: list(x),
        'percent_new_views': lambda x: list(x),
        'current_views': lambda x: x.iloc[-1]
    }).reset_index()

    max_days = int(round(max_days))
    
    columns = ["ID поста", "Дата публикации", "Текущие просмотры"] + [f"{i} д" for i in range(1, max_days+1)]
    data = []
    
    for _, row in reversed(list(grouped_df.iterrows())):
        view_change = row['view_change']
        percent_new_views = row['percent_new_views']
        current_views = row['current_views']
        
        row_data = [
            row['post_id'],
            datetime.strptime(str(row['post_datetime']), '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y'), #'%Y-%m-%d %H:%M:%S.%f'
            current_views
        ]
        for day in range(1, max_days+1):
            if day <= len(view_change):
                cell_value = f"{view_change[day-1]} ({percent_new_views[day-1]:.2f}%)"
                row_data.append(cell_value)
            else:
                row_data.append("-")
     
        data.append(row_data)

    df = pd.DataFrame(data, columns=columns)

    return df


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
                return 'color: orange'
            
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
        
        # Отображаем отформатированный DataFrame
        
    
        return styled_df
