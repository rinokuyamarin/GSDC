from flask import Flask, render_template, request, redirect, url_for
import csv, random
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)

# CSVファイルのパス
CSV_FILE_PATH = 'diary_data.csv'

# アップロードされたファイルの許可された拡張子
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# アップロードされたファイルの拡張子をチェック
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 感情分析モデルの初期化関数
def initialize_sentiment_analysis_model():
    model = AutoModelForSequenceClassification.from_pretrained("jarvisx17/japanese-sentiment-analysis")
    tokenizer = AutoTokenizer.from_pretrained("jarvisx17/japanese-sentiment-analysis")
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    return nlp

# 初期化済みの感情分析モデルを取得
nlp = initialize_sentiment_analysis_model()

# データをCSVファイルに書き込む
def write_to_csv(data):
    with open(CSV_FILE_PATH, 'a', newline='') as csvfile:
        fieldnames = ['date', 'content', 'score', 'image']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if csvfile.tell() == 0:
            writer.writeheader()
            
        writer.writerow(data)

# CSVファイルからデータを読み込む
def read_from_csv():
    data = []
    with open(CSV_FILE_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

@app.route('/')
def index():
    yesterday_diary = get_yesterday_diary()  # 追加
    return render_template('index.html', yesterday_diary=yesterday_diary)  # 追加

def get_yesterday_diary():
    diary_data = read_from_csv()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_diary = [entry for entry in diary_data if entry['date'] == yesterday]
    return random.choice(yesterday_diary) if yesterday_diary else None

UPLOAD_FOLDER = 'static/images'

@app.route('/submit_diary', methods=['POST'])
def submit_diary():
    if request.method == 'POST':
        diary_content = request.form.get('diary_content')
        image = request.files['image']  # フォームから画像ファイルを取得
        image_filename = None  # 初期値を設定

        image = request.files['image']
        image_filename = image.filename if image else None
        print("image_filename:", image_filename)  # 追加

        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image.save(image_path)
            
        # 感情分析モデルの初期化関数を呼び出してモデルを取得
        nlp = initialize_sentiment_analysis_model()
        sentiment_score = nlp(diary_content)[0]['score']


        #現在の日時を取得して、フォーマットを指定して文字列として保存

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d')
        # データをCSVファイルに書き込む
        data_to_write = {'date': formatted_datetime, 'content': diary_content, 'score': sentiment_score, 'image': image_filename}
        write_to_csv(data_to_write)

    return redirect(url_for('graph'))

@app.route('/graph')
def graph():
    diary_data = read_from_csv()
    return render_template('graph.html', diary_data=diary_data)


@app.route('/diary/<int:diary_id>')
def diary_details(diary_id):
    diary_data = read_from_csv()
    diary = diary_data[diary_id]
    return render_template('diary_details.html', diary=diary, image_filename=diary['image'])

if __name__ == '__main__':
    app.run(debug=True)