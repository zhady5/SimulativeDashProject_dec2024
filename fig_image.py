import streamlit as st
from wordcloud import WordCloud
import base64
from io import BytesIO
import string
import pandas as pd
from collections import Counter
import re
from functions import  gradient_color_func #get_gradient_color,

def load_stopwords_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        stopwords = [line.strip() for line in file]
    return stopwords

file_path = 'stopwords-ru.txt'
puncts = set(list(string.punctuation) + ['—', '»', '«', '``', '–', "''"])
stopwords_ru = set(load_stopwords_from_file(file_path))
predlogi = set(['без' , 'в' , 'до' , 'для' , 'за' , 'из' , 'к' , 'на' , 'над' , 'о' , 'об' , 'от' , 'по' , 'под' , 'пред' , 'при' , 'про' , 'с' , 'у' , 'через'])
souzy = set(['а' , 'и' , 'чтобы' , 'если', 'потому что' , 'как будто' , 'то есть'])
exclude = set(['например', 'какие', 'кто-то', 'что-то', 'кстати', 'многие', 'таких', 'может', 'любой', 'поэтому', 'https'])
numbers = set('1234567890')
dell_words = stopwords_ru | predlogi | souzy | numbers | exclude


# Функция для очистки текста
def clean_text(text):
    text = text.lower()  # Приводим весь текст к нижнему регистру
    text = re.sub(r'[^\w\s]', '', text)  # Удаляем все символы, кроме букв и пробелов
    words = text.split()  # Разбиваем текст на слова
    #stop_words = {'и', 'в', 'во', 'не', 'что', 'он', 'она', 'оно', 'они', 'но', 'а', 'это'}  # Простые стоп-слова
    words = [word for word in words if word not in dell_words]  # Удаляем стоп-слова
    return words
    

@st.cache_data
def prepare_data(posts, channel):
    posts_channel = posts[posts['channel_name'] == channel]
    words = posts_channel.text.apply(lambda t: clean_text(t)).tolist()
    df_words = pd.DataFrame(Counter(sum(words, [])).most_common(50), columns=['word', 'count'])
    return df_words

def plot_wordcloud(data, bgcolor ='#f5dfbf'):
    d = {a: x for a, x in data.values}
    wc = WordCloud(background_color=bgcolor, color_func=gradient_color_func)  # , width=480, height=360
    wc.fit_words(d)
    return wc.to_image()

def make_image(df_words, bgcolor ='#f5dfbf'):
    img = BytesIO()
    plot_wordcloud(data=df_words, , bgcolor ).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
