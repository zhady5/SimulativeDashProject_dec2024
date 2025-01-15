import streamlit as st
from wordcloud import WordCloud
import base64
from io import BytesIO
import string
import pandas as pd
from collections import Counter
import re
from preparation_data.functions import  gradient_color_func 

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

def plot_wordcloud(data):
    d = {a: x for a, x in data.values}
    wc = WordCloud(background_color='#f5dfbf', color_func=gradient_color_func(start_color_words, end_color_words))  # , width=480, height=360, 
    wc.fit_words(d)
    return wc.to_image()

def make_image(df_words, contr_color = '#f5dfbf', start_color_words = '#8B0000', end_color_words = '#ffb347'):
    img = BytesIO()
    d = {a: x for a, x in df_words.values}
    wc = WordCloud(background_color='#f5dfbf', colormap='Meerkat') #start_color = '#8B0000', end_color = '#ffb347'
    wc.fit_words(d)
    wc.to_image().save(img, format='PNG')
    #plot_wordcloud(data=df_words).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
