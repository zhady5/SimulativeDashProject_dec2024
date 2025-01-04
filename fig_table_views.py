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
            datetime.astype(str).strptime(row['post_datetime'], '%Y-%m-%d %H:%M:%S.%f').strftime('%b %d, %Y'),
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
