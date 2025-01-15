import datetime
from dateutil.relativedelta import relativedelta
from PIL import ImageColor
import pandas as pd
import random

def date_ago(tp, num=0):
    if tp == 'today':
        return datetime.datetime.now().strftime("%Y-%m-%d") 
    elif tp == 'yesterday':
        return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif tp == 'days':
        return (datetime.datetime.now() - datetime.timedelta(days=num+1)).strftime("%Y-%m-%d")
    elif tp == 'weeks':
        return (datetime.datetime.now() - datetime.timedelta(days= 7*num + 1)).strftime("%Y-%m-%d") 
    elif tp == 'months':
        return (datetime.datetime.now() - relativedelta(months=num) - datetime.timedelta(days=1)).strftime("%Y-%m-%d") 
    else:
        print('Неправильно задан тип даты или не указано количество повторений (возможные типы дат: today, yesterday, days, weeks, months')

def convert_date(date, format_date = '%Y-%m-%d %H:%M:%S.%f'):
    try:
        return datetime.datetime.strptime(date, format_date)
    except ValueError:
        # Если строка не может быть преобразована в дату, возвращаем NaT (Not a Time)
        return pd.NaT


def get_current_previous_sums(df, col, period):
    mask1 = (df.date.apply(lambda d: convert_date(d, '%Y-%m-%d').date()) <= convert_date(date_ago(period[0]), '%Y-%m-%d').date())
    mask2 = (df.date.apply(lambda d: convert_date(d, '%Y-%m-%d').date()) > convert_date(date_ago(period[1], period[2]), '%Y-%m-%d').date())
    mask3 = (df.date.apply(lambda d: convert_date(d, '%Y-%m-%d').date()) <= convert_date(date_ago(period[1], period[2]), '%Y-%m-%d').date())
    mask4 = (df.date.apply(lambda d: convert_date(d, '%Y-%m-%d').date()) > convert_date(date_ago(period[1], period[2]*2), '%Y-%m-%d').date())
    
    current = df[mask1&mask2][col].sum()
    previous = df[mask3&mask4][col].sum()    
    
    return current, previous


# Функция для определения градиентной заливки
def get_gradient_color(value, min_val=0, max_val=100):
    # Если значение равно нулю, возвращаем прозрачный цвет
    if value == 0:
        return "transparent"
    
    # Рассчитываем процентное соотношение между минимальным и максимальным значением
    ratio = (value - min_val) / (max_val - min_val)
    # Ограничиваем диапазон значений
    ratio = max(min(ratio, 1), 0)

     # Начальные и конечные значения RGB
    start_r, start_g, start_b = 139, 0, 0 #245, 223, 191  # Бежевый (#f5dfbf)
    end_r, end_g, end_b = 34, 139, 34          # Зелёный (#228B22)
    
    # Рассчитываем промежуточные значения RGB
    r = int(start_r * (1 - ratio) + end_r * ratio)
    g = int(start_g * (1 - ratio) + end_g * ratio)
    b = int(start_b * (1 - ratio) + end_b * ratio)
    
    color = '#%02x%02x%02x' % (r, g, b)
    return color


def hex_to_rgb(hex_code):
    """Преобразует HEX-код в RGB."""
    rgb = ImageColor.getcolor(hex_code, "RGB")
    return rgb

def interpolate_color(start_color, end_color, steps):
    """Интерполирует цвет между двумя значениями RGB."""
    start_r, start_g, start_b = start_color
    end_r, end_g, end_b = end_color
    step_r = (end_r - start_r) / steps
    step_g = (end_g - start_g) / steps
    step_b = (end_b - start_b) / steps
    return [(int(start_r + i * step_r),
             int(start_g + i * step_g),
             int(start_b + i * step_b)) for i in range(steps)]

def gradient_color_func(start_color = '#8B0000', end_color = '#ffb347', word=None, font_size=None, position=None, orientation=None, font_path=None, random_state=None):
    start_color = hex_to_rgb(start_color)
    end_color = hex_to_rgb(end_color)
    num_steps = 50  # Количество шагов равно количеству слов
    colors = interpolate_color(start_color, end_color, num_steps)
    index = random.randint(0, num_steps - 1)  # Случайное число от 0 до количества слов
    r, g, b = colors[index]
    return f"rgb({r}, {g}, {b})"



# ОСНОВНЫЕ ХАРАКТЕРИСТИКИ КАНАЛА

# В среднем приходится просмотров на 1й день от всех просмотров
# В среднем приходится просмотров на 1ю неделю от всех просмотров
#-----------------------------Метрики по подписчикам-------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------

def calculate_mean_max_subs(subs, channel):
    filtered_df = subs[subs.channel_name==channel][['date', 'day_change_pos', 'day_change_neg']].drop_duplicates()
    
    # вопрос по округлению!!!!!!!
    mean_subs_pos, mean_subs_neg = int(round(filtered_df.day_change_pos.mean(), 0)), int(round(filtered_df.day_change_neg.mean(), 0)) 
    max_subs_pos, max_subs_neg = int(round(filtered_df.day_change_pos.max(), 0)), int(round(filtered_df.day_change_neg.min(), 0)) 
    
    # Средний ежедневный прирост
    # Средний ежедневный отток    
    # Максимальный дневной прирост 
    # Максимальный дневной отток
    
    return mean_subs_pos, mean_subs_neg, max_subs_pos, max_subs_neg

#-----------------------------Метрики по публикациям-------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------

def calculate_mean_posts(posts, channel):
    filtered_df = posts[posts.channel_name==channel].copy()
    filtered_df.loc[:, 'date_week'] = pd.to_datetime(filtered_df.date).apply(lambda d: d.isocalendar().week)
    filtered_df.loc[:, 'date_month'] = filtered_df.date.apply(lambda d: str(d)[:7])

    mean_posts_day = int(round(filtered_df.cnt.sum()/len(pd.date_range(filtered_df.date.min(), filtered_df.date.max())), 0))
    mean_posts_week = int(round(filtered_df.groupby('date_week').cnt.sum().mean(), 0))
    mean_posts_month = int(round(filtered_df.groupby('date_month').cnt.sum().mean(), 0))

    # среднее количество публикаций в день
    # среднее количество публикаций в неделю
    # среднее количество публикаций в месяц

    return mean_posts_day, mean_posts_week, mean_posts_month

#-----------------------------Метрики по просмотрам-------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------

def calculate_mean_views(post_view, channel):
    filtered_df = post_view[post_view.channel_name==channel].copy()
    mean_views = int(round(filtered_df[['post_id', 'current_views']].drop_duplicates().current_views.mean(), 0))
    
    # Среднее количество просмотров одной публикации
    
    return mean_views 

#-----------------------------Метрики по реакциям-------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------

def calculate_mean_reacts(gr_pvr, channel, react1='', perc1=0, react2='', perc2=0, react3='', perc3=0):
    filtered_df = gr_pvr[gr_pvr.channel_name == channel]

    filtered_df.loc[:,'reaction_type'] = filtered_df.reaction_type.apply(lambda r: 'Custom' if 'ReactionCustomEmoji' in r else r)
    filtered_df.loc[:,'reaction_type'] = filtered_df.reaction_type.apply(lambda r: 'Paid 🌟' if 'ReactionPaid' in r else r)
    
    mean_reacts = int(round(filtered_df[['post_id', 'react_cnt_sum']].drop_duplicates().react_cnt_sum.mean(), 0))
    mean_idx = round(filtered_df[['post_id', 'idx_active']].drop_duplicates().idx_active.mean(), 1)
    
    allReact = filtered_df.react_cnt.sum()
    top3react = filtered_df.groupby('reaction_type').react_cnt.sum().reset_index()\
                            .sort_values('react_cnt', ascending=False).head(3).reset_index()
    top3react.loc[:, 'react_cnt_perc'] = round(top3react.react_cnt/allReact*100, 0)
    cnt_react = top3react.shape[0]
    
    if cnt_react == 3:
        react1, perc1 = top3react.reaction_type[0], int(top3react.react_cnt_perc[0])
        react2, perc2 = top3react.reaction_type[1], int(top3react.react_cnt_perc[1])
        react3, perc3 = top3react.reaction_type[2], int(top3react.react_cnt_perc[2])
    elif cnt_react == 2:
        react1, perc1 = top3react.reaction_type[0], int(top3react.react_cnt_perc[0])
        react2, perc2 = top3react.reaction_type[1], int(top3react.react_cnt_perc[1])
    elif cnt_react == 1:
        react1, perc1 = top3react.reaction_type[0], int(top3react.react_cnt_perc[0])

    # Среднее количество реакций на публикацию
    # Средний индекс активности
    # 3 самых популярных реакий и их доли от всех реакций 

    return mean_reacts, mean_idx, react1, perc1, react2, perc2, react3, perc3


#def load_stopwords_from_file(file_path):
#    with open(file_path, 'r', encoding='utf-8') as file:
#        stopwords = [line.strip() for line in file]
#    return stopwords


