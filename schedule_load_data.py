import pandas as pd
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
import io

import schedule
import time
import csv
import base64
import requests
import json

load_dotenv(dotenv_path='.gitignore/.env') 

# Функция для подключения к базе данных
def connect_to_db():
    db_name = os.environ.get('DB_NAME')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    host = os.environ.get('DB_HOST')
    port = int(os.environ.get('DB_PORT'))

    return psycopg2.connect(
        host=host,
        dbname=db_name,
        user=user,
        password=password,
        port=port
    )

def fetch_dataframe(cursor, query, params=None):
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    return pd.DataFrame(cursor.fetchall(), columns=columns)

def dataframe_to_csv(df):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue().encode()).decode()


def upload_to_github(encoded_data, repo_owner, repo_name, branch, github_token, file_path):
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Получаем информацию о последнем коммите в указанной ветви
    branch_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch}"
    branch_response = requests.get(branch_url, headers=headers)
    branch_response.raise_for_status()
    last_commit_sha = branch_response.json()["commit"]["sha"]

    # Создаем имя временного файла
    temp_file_path = f"{file_path.rsplit('.', 1)[0]}_temp.{file_path.rsplit('.', 1)[1]}"

    # Создаем временный файл
    temp_update_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{temp_file_path}"
    temp_commit_message = f"Create temporary file {temp_file_path}"
    temp_payload = {
        "message": temp_commit_message,
        "content": encoded_data,
        "branch": branch
    }

    temp_response = requests.put(temp_update_url, data=json.dumps(temp_payload), headers=headers)
    if temp_response.status_code not in (200, 201):
        print(f"Ошибка при создании временного файла {temp_file_path}: {temp_response.text}")
        temp_response.raise_for_status()
    else:
        print(f"Временный файл {temp_file_path} успешно создан!")

    # Проверяем существование основного файла
    content_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    content_response = requests.get(content_url, headers=headers, params={"ref": branch})
    
    if content_response.status_code == 200:
        # Файл существует, удаляем его
        sha = content_response.json()["sha"]
        delete_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        delete_payload = {
            "message": f"Delete old {file_path} before replacing",
            "sha": sha,
            "branch": branch
        }
        delete_response = requests.delete(delete_url, data=json.dumps(delete_payload), headers=headers)
        if delete_response.status_code == 200:
            print(f"Старый файл {file_path} удалён!")
        else:
            print(f"Ошибка при удалении старого файла {file_path}: {delete_response.text}")
            delete_response.raise_for_status()

    # Переименовываем временный файл в основной
    rename_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    rename_payload = {
        "message": f"Rename {temp_file_path} to {file_path}",
        "content": encoded_data,
        "sha": temp_response.json()["content"]["sha"],
        "branch": branch
    }
    rename_response = requests.put(rename_url, data=json.dumps(rename_payload), headers=headers)
    if rename_response.status_code in (200, 201):
        print(f"Временный файл переименован в {file_path}. Данные обновлены!")
    else:
        print(f"Ошибка при переименовании файла: {rename_response.text}")
        rename_response.raise_for_status()

    # Удаляем временный файл, если он остался
    delete_temp_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{temp_file_path}"
    delete_temp_payload = {
        "message": f"Delete temporary file {temp_file_path}",
        "sha": temp_response.json()["content"]["sha"],
        "branch": branch
    }
    delete_temp_response = requests.delete(delete_temp_url, data=json.dumps(delete_temp_payload), headers=headers)
    if delete_temp_response.status_code == 200:
        print(f"Временный файл {temp_file_path} удалён.")
    else:
        print(f"Произошла ошибка при удалении временного файла: {delete_temp_response.text}")

    return rename_response.json()

# Основная функция для планирования задачи
def job():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        six_month_ago = datetime.now() - timedelta(days=180)

        # CHANNELS
        channels = fetch_dataframe(cursor, "SELECT * FROM channels")
        channels_csv = dataframe_to_csv(channels)
        
        # POSTS
        posts_query = sql.SQL("SELECT * FROM posts WHERE date >= %s;")
        posts = fetch_dataframe(cursor, posts_query, (six_month_ago,))
        posts_csv = dataframe_to_csv(posts)
        
        # SUBSCRIBERS
        subscribers_query = sql.SQL("SELECT * FROM subscribers WHERE timestamp >= %s;")
        subscribers = fetch_dataframe(cursor, subscribers_query, (six_month_ago,))
        subscribers_csv = dataframe_to_csv(subscribers)
        
        # VIEWS
        post_ids = tuple(posts['id'].tolist())
        views_query = sql.SQL("SELECT * FROM views WHERE post_id IN %s;")
        views = fetch_dataframe(cursor, views_query, (post_ids,))
        views_csv = dataframe_to_csv(views)
        
        # REACTIONS
        reactions_query = """
            WITH ranked_reacts AS (
                SELECT *, 
                    ROW_NUMBER() OVER (PARTITION BY post_id, reaction_type ORDER BY timestamp DESC) AS rn
                FROM reactions
            )
            SELECT *
            FROM ranked_reacts
            WHERE rn = 1;
        """
        reactions = fetch_dataframe(cursor, reactions_query)
        reactions_csv = dataframe_to_csv(reactions)

        cursor.close()
        conn.close()

        # Загрузка данных в репозиторий GitHub
        github_token = os.environ.get("GITHUB_TOKEN")
        repo_owner = "zhady5"
        repo_name = "SimulativeDashProject_dec2024"
        branch = "master"

        file_paths = {
            "channels": "data/channels.csv",
            "posts": "data/posts.csv",
            "subscribers": "data/subscribers.csv",
            "views": "data/views.csv",
            "reactions": "data/reactions.csv"
        }

        for table, file_path in file_paths.items():
            csv_data = locals()[f"{table}_csv"]
            upload_to_github(csv_data, repo_owner, repo_name, branch, github_token, file_path)

    except Exception as e:
        print(f"Ошибка при выполнении задания: {e}")


# Расписание задач в Московском времени (GMT+3)
utc_offset = 2  # Разница между Московским временем и Екатеринбургским временем
# Преобразуем время в UTC
def utc_time(hour, mins=0):
    now_utc = datetime.utcnow()
    target_hour = hour + utc_offset
    if target_hour > 24:
        target_hour -= 24
    return str(now_utc.replace(hour=target_hour, minute=mins, second=0, microsecond=0))[11:16]


# Настраиваем расписание
schedule.every().day.at(utc_time(1)).do(job)
schedule.every().day.at(utc_time(5)).do(job)
schedule.every().day.at(utc_time(9)).do(job)
schedule.every().day.at(utc_time(13)).do(job)
schedule.every().day.at(utc_time(17)).do(job)
schedule.every().day.at(utc_time(21)).do(job)

while True:
    schedule.run_pending()
    time.sleep(60)



## Планирование задачи
#schedule.every().day.at("00:00").do(job)
#schedule.every().day.at("01:00").do(job)
#schedule.every().day.at("05:00").do(job)
#schedule.every().day.at("09:00").do(job)
#schedule.every().day.at("13:00").do(job)
#schedule.every().day.at("17:00").do(job)
#schedule.every().day.at("21:00").do(job)
#
#while True:
#    schedule.run_pending()
#    time.sleep(1)