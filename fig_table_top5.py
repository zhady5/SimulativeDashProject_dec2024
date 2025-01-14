import streamlit as st
import os
import math
from numbers import Number
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
    
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

from plottable import ColumnDefinition, Table
from plottable.cmap import normed_cmap
#from plottable.formatters import decimal_to_percent
from plottable.plots import circled_image # image


def create_table_top5(posts, subs, gr_pvr,  channel, color_phone='#FFA500'):
    
    def df_cnt_sub_between_posts(posts, subs, channel):
        p = posts[['id', 'datetime', 'channel_name' 
                      ]][posts.channel_name == channel].sort_values(by='datetime').copy()
        p.columns = ['post_id', 'datetime', 'channel_name']
        p['datetime'] = p['datetime'].apply(lambda d: pd.Timestamp(d))

        s = subs[['id', 'datetime', 'subs_cnt', 'channel_name','subs_change', 'subs_change_pos', 'subs_change_neg'
                                                                 ]][subs.channel_name == channel].sort_values(by='datetime').copy()
        s['datetime'] = s['datetime'].apply(lambda d: pd.Timestamp(d))

        df = pd.merge_asof(s, p, on='datetime', by = 'channel_name')
    
        return df.groupby(['channel_name', 'post_id'])[['subs_change', 'subs_change_pos', 'subs_change_neg']].sum().reset_index()
    
    
    post_subs_changes = df_cnt_sub_between_posts(posts, subs, channel)
    
    df_cols = ['channel_name', 'post_id','post_datetime', 'current_views', 
             'react_cnt_sum', 'idx_active']
    df = gr_pvr[df_cols][gr_pvr.channel_name == channel].sort_values(by='current_views', ascending=False).drop_duplicates()
    
    def get_top_bottom(df, col, n=5):
        top5_views = df.nlargest(n, col)[['post_id', col]]
        bottom5_views = df.nsmallest(n, col)[['post_id', col]].sort_values(by = col, ascending=False)
        
        # Исключаем строки с NaN перед конкатенацией
        top5_views = top5_views.dropna(how='all')
        bottom5_views = bottom5_views.dropna(how='all')
        
        return pd.concat([top5_views,  bottom5_views], axis=0).reset_index(drop=True)
    
    data_views = get_top_bottom(df, 'current_views', 5)
    data_react_sum = get_top_bottom(df, 'react_cnt_sum', 5)
    data_idx_active = get_top_bottom(df, 'idx_active', 5)
    
    data_post_subs_pos = post_subs_changes.nlargest(5, 'subs_change_pos')[['post_id', 'subs_change_pos']].rename(columns={'subs_change_pos': 'subs_change'})
    data_post_subs_neg = post_subs_changes.nsmallest(5, 'subs_change_neg')[['post_id', 'subs_change_neg']].rename(columns={'subs_change_neg': 'subs_change'}).sort_values(by='subs_change', ascending=False)

    
    data_post_subs = pd.concat([data_post_subs_pos, data_post_subs_neg], axis=0).reset_index(drop=True)
    
    df = pd.concat([data_views,  data_react_sum ,  data_idx_active, data_post_subs], axis=1)
    
    df.columns = ['ID поста (1)' , 'Текущее количество'
                  ,'ID поста (2)' , 'Общее количество'
                   ,'ID поста (3)' , 'Индекс'
                 ,'ID поста (4)' , 'Подписались\Отписались'
                 ]
    
    df = df.set_index('ID поста (1)')
    
    #cmap_colors = 
    cmap_colors =  matplotlib.cm.autumn  #matplotlib.cm.get_cmap('afmhot').reversed()
    
    cmap = LinearSegmentedColormap.from_list(
        name="lavender_to_midnight", colors= ['#FFFFFF', '#E6E6FA', '#9370DB', '#4B0082', '#191970'], N=256
    )   
    #["#ffffff", "#f2fbd2", "#c9ecb4", "#93d3ab", "#35b0ab"]
    
    basic_services_cols = ['Текущее количество', 'Общее количество', 'Индекс', 'Подписались\Отписались']
    
    
    #PiYG
    col_defs = (
        [
            ColumnDefinition(
                name="ID поста (1)",
                textprops={"ha": "center", "weight": "bold", "fontsize":11},
                width=0.6,
                group="Просмотры",
            ),
              ColumnDefinition(
                name="Текущее количество",
                width=0.65,
                textprops={
                    "ha": "center",
                    "bbox": {"boxstyle": "circle", "pad": 0.95},
                    "fontsize":11
                },
                cmap=normed_cmap(df["Текущее количество"], cmap=cmap_colors, num_stds=1), #matplotlib.cm.plasma
                group="Просмотры",
    
            ),
    
            ColumnDefinition(
                name="ID поста (2)",
                textprops={"ha": "right", "weight": "bold", "fontsize":11},
                width=0.6,
                group="Реакции",
            ),
                 ColumnDefinition(
                name="Общее количество",
                width=0.65,
                textprops={
                    "ha": "center",
                    "bbox": {"boxstyle": "circle", "pad": 0.65},
                    "fontsize":11
                },
                cmap=normed_cmap(df["Общее количество"], cmap=cmap_colors, num_stds=1),
                group="Реакции",
            ),
    
            ColumnDefinition(
                name="ID поста (3)",
                textprops={"ha": "right", "weight": "bold", "fontsize":11},
                width=0.6,
                group="Вовлеченность",
            ),
              ColumnDefinition(
                name="Индекс",
                width=0.65,
                textprops={
                    "ha": "center",
                    "bbox": {"boxstyle": "circle", "pad": 0.55},
                    "fontsize":11
                },
                cmap=normed_cmap(df["Индекс"], cmap=cmap_colors, num_stds=1),
                group="Вовлеченность",
            ),
    
                    ColumnDefinition(
                name="ID поста (4)",
                textprops={"ha": "right", "weight": "bold", "fontsize":11},
                width=0.6,
                group="Подписчики после публикации поста",
            ),
              ColumnDefinition(
                name="Подписались\Отписались",
                width=0.65,
                textprops={
                    "ha": "center",
                    "bbox": {"boxstyle": "circle", "pad": 0.55},
                    "fontsize":11
                },
                cmap=normed_cmap(df["Подписались\Отписались"], cmap=cmap_colors, num_stds=1),
                group="Подписчики после публикации поста",
            ),
            
        ])
    
    plt.rcParams["font.family"] = ["DejaVu Sans"]
    plt.rcParams["savefig.bbox"] = "tight"
    
    df = df.fillna('')
    
    def is_number(obj):
        return isinstance(obj, Number)
        
    #for n in [4,5]:
    #    df[f'ID поста ({n})'] = df[f'ID поста ({n})'].apply(lambda c: str(c)[:-2] if is_number(c) else c)
    
    fig, ax = plt.subplots(figsize=(20, 22))
    
    # Set the figure and axes background to orange
    fig.patch.set_facecolor(color_phone) ##f5dfbf #'#FFA500'
    ax.set_facecolor(color_phone)
    
    table = Table(
        df,
        column_definitions=col_defs,
        row_dividers=True,
        footer_divider=True,
        ax=ax,
        textprops={"fontsize": 14, 'color': '#666'},
        row_divider_kw={"linewidth": 1, "linestyle": (0, (1, 5))},
        col_label_divider_kw={"linewidth": 1, "linestyle": "-"},
        column_border_kw={"linewidth": 1, "linestyle": "-"},
    )
        
    # Adding the bold header as a text annotation
    header_text = "\n Лидеры и аутсайдеры среди постов"
    header_props = {'fontsize': 18, 'fontweight': 'bold', 'va': 'center', 'ha': 'center', 'color': '#666'}
    # Adjusting the y-coordinate to bring the header closer to the table
    plt.text(0.5, 0.91, header_text, transform=fig.transFigure, **header_props)
    
    # Adding the subtitle at the top in gray
    subtitle_text = "\n Все посты сравниваются в рамках одного канала. \n Отображаются топ-5 постов с наивысшими показателями и топ-5 с наихудшими показателями на текущий момент. "
    subtitle_props = {'fontsize': 14, 'va': 'center', 'ha': 'center', 'color': '#666'}
    plt.text(0.5, 0.89, subtitle_text, transform=fig.transFigure, **subtitle_props)
    
    # Adding the footer text
    footer_text = "Источник: Данные Telegram API"
    footer_props = {'fontsize': 14, 'va': 'center', 'ha': 'center', 'color': '#666'}
    # Adjusting the y-coordinate to position the footer closer to the bottom of the figure
    plt.text(0.5, 0.09, footer_text, transform=fig.transFigure, **footer_props)
    
    fig.savefig("tableTopBottom.png", facecolor=ax.get_facecolor(), dpi=200)
    # Закрываем текущий график
    plt.close(fig)

    return fig
