import plotly
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from functions import get_current_previous_sums


def create_fig_posts_inds(posts, selected_channel, bgcolor='#ffb347'):
    
    # График по публикациям
    subdf_posts = posts[posts.channel_name == selected_channel][['channel_name', 'date', 'cnt']].drop_duplicates()
    
    # Создание subplots
    fig_posts = make_subplots(
        rows=3,
        cols=2,
        specs=[
            [{"rowspan": 3}, {'type': 'indicator'}],
            [None, {'type': 'indicator'}],
            [None, {'type': 'indicator'}],
        ],
        vertical_spacing=0.08
    )
    
    mean_cnt = subdf_posts.cnt.mean()
    colors = ['#8B4513' if val >= 2 * mean_cnt else '#F5DEB3' for val in subdf_posts['cnt']]
    
    fig_posts.add_trace(go.Bar(x=subdf_posts.date, y=subdf_posts.cnt, marker_color=colors,
                               hovertemplate='%{x} <br>Публикаций: %{y}<extra></extra>'), row=1, col=1)
    
    period_names = dict({'days': 'вчера', 'weeks': 'неделю', 'months': 'месяц'})
    for i, period in enumerate([('days', 'days', 1), ('weeks', 'weeks', 1), ('months', 'months', 1)]):
        current, previous = get_current_previous_sums(subdf_posts, 'cnt', period)
        
        fig_posts.add_trace(
            go.Indicator(
                value=current,
                title={"text": f"<span style='font-size:0.8em;color:gray'>Публикаций за {period_names[period[0]]}</span>"},
                mode="number+delta",
                delta={'reference': previous, 'relative': True, "valueformat": ".2%"},
            ), row=i + 1, col=2
        )
    
    # Настройка стиля графика
    fig_posts.update_layout(
        template="simple_white",
        font_family="Georgia",
        font_size=12,
        margin=dict(l=40, r=20, t=40, b=10),
        paper_bgcolor= bgcolor, #'#ffb347', #'rgba(0,0,0,0)',
        plot_bgcolor= bgcolor, #'rgba(0,0,0,0)',
        xaxis=dict(
            rangeselector=dict(  # Добавляем элементы управления диапазоном
                bgcolor='#f5dfbf',  # Фоновый цвет области с кнопками
                font=dict(color="#333"),  # Цвет текста на кнопках
                activecolor=bgcolor,  # Цвет активной кнопки
                bordercolor='#f5dfbf',  # Цвет рамки вокруг кнопок
                buttons=list([
                    dict(count=2, label="2д", step="day", stepmode="backward"),
                    dict(count=14, label="2н", step="day", stepmode="backward"),
                    dict(count=2, label="2м", step="month", stepmode="backward"),
                    dict(step="all")  # Кнопка для просмотра всего диапазона
                ])
            )
        )
    )
    return fig_posts
