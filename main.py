from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp, requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Twitter Downloader API Running!"

@app.route('/get-info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url', '')
    if not url:
        return jsonify({'error': 'No URL'}), 400

    strategies = [
        {
            'quiet': True, 'no_warnings': True,
            'format': 'best/bestvideo+bestaudio',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            }
        },
        {
            'quiet': True, 'no_warnings': True,
            'format': 'best',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/107.0.0.0 Mobile Safari/537.36',
            }
        }
    ]

    info = None
    for opts in strategies:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info: break
        except: continue

    if not info:
        return jsonify({'error': 'Could not fetch video'}), 500

    formats = []
    for f in info.get('formats', []):
        if f.get('url') and f.get('ext') in ['mp4', 'webm']:
            formats.append({
                'quality': str(f.get('format_note', f.get('height', 'HD'))),
                'ext': f.get('ext', 'mp4'),
                'url': f.get('url', '')
            })

    return jsonify({
        'title': info.get('title', 'Twitter Video'),
        'thumbnail': info.get('thumbnail', ''),
        'platform': info.get('extractor', 'twitter'),
        'download_url': info.get('url', ''),
        'formats': formats[-6:]
    })

@app.route('/proxy-download', methods=['GET'])
def proxy_download():
    video_url = request.args.get('url', '')
    filename = request.args.get('filename', 'video')
    ext = request.args.get('ext', 'mp4')
    if not video_url:
        return jsonify({'error': 'No URL'}), 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://twitter.com/',
    }
    try:
        r = requests.get(video_url, headers=headers, stream=True, timeout=60)
        return Response(
            stream_with_context(r.iter_content(chunk_size=1024*1024)),
            headers={
                'Content-Disposition': f'attachment; filename="{filename}.{ext}"',
                'Content-Type': r.headers.get('Content-Type', f'video/{ext}'),
                'Access-Control-Allow-Origin': '*',
                'Content-Length': r.headers.get('Content-Length', '')
            }, status=200
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
