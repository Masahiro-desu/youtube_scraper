# app.py
from flask import Flask, render_template, jsonify
from models import db, Video
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
db.init_app(app)

API_KEY = 'AIzaSyBlgse05Q8qQGQCJpkzTRdT55F3QD_6U2M'  # ここにあなたのAPIキーを設定してください

def fetch_youtube_videos(region_code, max_results=10):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    video_url = "https://www.googleapis.com/youtube/v3/videos"
    channel_url = "https://www.googleapis.com/youtube/v3/channels"

    # 検索クエリを設定
    search_params = {
        'part': 'snippet',
        'maxResults': max_results * 2,  # 余裕を持って取得
        'order': 'viewCount',
        'publishedAfter': '2023-07-31T00:00:00Z',
        'type': 'video',
        'regionCode': region_code,
        'key': API_KEY
    }

    r = requests.get(search_url, params=search_params)
    results = r.json()['items']

    video_ids = [result['id']['videoId'] for result in results]
    channel_ids = [result['snippet']['channelId'] for result in results]

    # ビデオ情報を取得
    video_params = {
        'part': 'snippet,statistics',
        'id': ','.join(video_ids),
        'key': API_KEY
    }

    r = requests.get(video_url, params=video_params)
    videos = r.json()['items']

    # チャンネル情報を取得
    channel_params = {
        'part': 'statistics',
        'id': ','.join(channel_ids),
        'key': API_KEY
    }

    r = requests.get(channel_url, params=channel_params)
    channels = r.json()['items']
    channel_data = {channel['id']: channel['statistics']['subscriberCount'] for channel in channels}

    # 動画情報を整形
    video_data = []
    for video in videos:
        video_url = f"https://www.youtube.com/watch?v={video['id']}" if video.get('id') else None
        channel_id = video['snippet']['channelId']
        if video_url:  # URLが存在する場合のみ処理を続行
            video_data.append({
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'views': int(video['statistics']['viewCount']),
                'subscribers': int(channel_data.get(channel_id, 0)),
                'genre': video['snippet'].get('categoryId', 'N/A'),
                'url': video_url
            })

    # 登録者数に対して再生回数が多い順にソートして上位10を返す
    sorted_videos = sorted(video_data, key=lambda x: x['views'] / max(x['subscribers'], 1), reverse=True)
    return sorted_videos[:10]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-videos')
def fetch_videos():
    # 日本の動画を取得
    jp_videos = fetch_youtube_videos('JP', 10)
    # 世界の動画を取得
    global_videos = fetch_youtube_videos('US', 10)

    videos = jp_videos + global_videos

    # データベースをリセットして保存
    Video.query.delete()
    for video in videos:
        new_video = Video(
            title=video['title'],
            channel=video['channel'],
            views=video['views'],
            subscribers=video['subscribers'],
            genre=video['genre'],
            url=video['url']  # URLフィールドを追加
        )
        db.session.add(new_video)
    db.session.commit()

    return jsonify(videos)

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # 既存のテーブルを削除
        db.create_all()  # テーブルを再作成
    app.run(debug=True)