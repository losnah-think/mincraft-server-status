from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from mcstatus import JavaServer
import logging
import datetime
import sqlite3
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Flask 설정
app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite DB 설정
db_name = 'server_status.db'

# 서버 호스트와 포트 환경 변수 설정
host = os.getenv('MINECRAFT_SERVER_HOST', '127.0.0.1')
port = int(os.getenv('MINECRAFT_SERVER_PORT', '25565'))

def init_db():
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS server_status (
                    timestamp TEXT,
                    online INTEGER,
                    players INTEGER,
                    max_players INTEGER,
                    ping INTEGER
                )''')
    conn.commit()
    conn.close()
    
# 리액트 앱 서빙을 위한 라우트 설정
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/status', methods=['GET'])
def get_server_status():
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        status = server.status()

        response = {
            "online": True,
            "players": status.players.online,
            "maxPlayers": status.players.max,
            "version": status.version.name,
            "motd": str(status.description),
            "ping": round(status.latency),
            "playersList": [player.name for player in status.players.sample] if status.players.sample else []
        }

        save_status_to_db(True, status.players.online, status.players.max, round(status.latency))

        return jsonify(response)

    except Exception as e:
        logging.error(f"Error connecting to {host}:{port} - {str(e)}")
        save_status_to_db(False, 0, 0, 0)
        return jsonify({
            "online": False,
            "error": str(e)
        })

@app.route('/historical', methods=['GET'])
def get_historical_data():
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        time_threshold = (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
        c.execute("SELECT * FROM server_status WHERE timestamp > ?", (time_threshold,))
        rows = c.fetchall()
        conn.close()

        historical_data = [
            {
                "timestamp": row[0],
                "online": bool(row[1]),
                "players": row[2],
                "maxPlayers": row[3],
                "ping": row[4]
            } for row in rows
        ]

        return jsonify(historical_data)

    except Exception as e:
        logging.error(f"Error fetching historical data - {str(e)}")
        return jsonify({"error": str(e)})

def save_status_to_db(online, players, max_players, ping):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO server_status (timestamp, online, players, max_players, ping) VALUES (?, ?, ?, ?, ?)",
                  (timestamp, int(online), players, max_players, ping))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving status to database - {str(e)}")

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 3001))  # Heroku에서 제공하는 PORT를 사용
    app.run(host='0.0.0.0', port=port)
