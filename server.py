import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# --- Configuración de logs a fichero ---
if not os.path.exists('logs'):
    os.mkdir('logs')
logger = logging.getLogger('turestaurante')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('logs/server.log', maxBytes=1_048_576, backupCount=5, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# --- Conexión a MySQL ---
try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Cornejo11.",
        database="restaurante",
        port=3307
    )
    logger.info("[OK] Conexión exitosa a MySQL")
except Error as e:
    logger.error(f"[ERROR] Conexión a MySQL: {e}")
    raise

# --- Ruta raíz ---
@app.route('/', methods=['GET'])
def home():
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Tu Restaurante - Inicio</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #fafafa; margin: 0; padding: 0; }
          header { background: #1976d2; color: white; padding: 1rem; text-align: center; }
          main { padding: 2rem; display: flex; justify-content: center; gap: 2rem; }
          a.card {
            text-decoration: none;
            width: 200px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 1.2rem;
            text-align: center;
            color: #1976d2;
            transition: transform .2s, box-shadow .2s;
          }
          a.card:hover {
            transform: translateY(-4px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
          }
          a.card h3 { margin: .5rem 0; }
        </style>
      </head>
      <body>
        <header>
          <h1>Tu Restaurante</h1>
        </header>
        <main>
          <a href="/pedidos" class="card">
            <h3>Ver Pedidos</h3>
            <p>Listado de pedidos realizados</p>
          </a>
          <a href="/logs" class="card">
            <h3>Ver Logs</h3>
            <p>Historial de actividad del servidor</p>
          </a>
        </main>
      </body>
    </html>
    """

# --- Endpoint para registrar un pedido ---
@app.route('/registrar_pedido', methods=['POST'])
def registrar_pedido():
    logger.info("🔔 POST /registrar_pedido recibido")
    try:
        data = request.get_json()
        logger.info(f"🔔 Payload: {data}")

        mozo       = data['mozo']
        mesa       = data['mesa']
        plato      = data['plato']
        comentario = data['comentario']
        precio     = data['precio']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO pedidos (mozo, mesa, plato, comentario, precio) VALUES (%s,%s,%s,%s,%s)",
            (mozo, mesa, plato, comentario, precio)
        )
        db.commit()
        cursor.close()

        logger.info("✅ Pedido insertado en BD")
        return jsonify({"message": "Pedido registrado exitosamente"}), 200

    except Error as e:
        logger.error(f"❌ Error al insertar pedido: {e}")
        return jsonify({"error": str(e)}), 500

# --- Endpoint para reiniciar pedidos ---
@app.route('/reiniciar', methods=['POST'])
def reiniciar_pedidos():
    logger.info("🔔 POST /reiniciar recibido")
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM pedidos")
        db.commit()
        cursor.close()
        logger.info("✅ Pedidos reiniciados")
        return jsonify({"message": "Pedidos reiniciados"}), 200
    except Error as e:
        logger.error(f"❌ Error al reiniciar pedidos: {e}")
        return jsonify({"error": str(e)}), 500

# --- Ruta para ver logs en HTML ---
@app.route('/logs', methods=['GET'])
def ver_logs():
    try:
        with open('logs/server.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()[-200:]
    except FileNotFoundError:
        lines = ["No hay logs aún."]

    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Logs del Servidor</title>
        <style>
          body { font-family: 'Courier New', monospace; background: #eceff1; margin: 0; padding: 2rem; }
          h2 { color: #37474f; }
          .log-container {
            background: #fff;
            padding: 1rem;
            border-radius: 6px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
          .line { margin-bottom: 0.3rem; color: #263238; }
        </style>
      </head>
      <body>
        <h2>Historial de Logs</h2>
        <div class="log-container">
          {% for line in lines %}
            <div class="line">{{ line|e }}</div>
          {% endfor %}
        </div>
      </body>
    </html>
    """
    return render_template_string(html, lines=lines)

# --- NUEVA RUTA: Mostrar los pedidos en HTML con tarjetas coloridas ---
@app.route('/pedidos', methods=['GET'])
def ver_pedidos():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT mozo, mesa, plato, comentario, precio, fecha FROM pedidos ORDER BY fecha DESC")
    pedidos = cursor.fetchall()
    cursor.close()

    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Pedidos Registrados</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; margin: 0; padding: 2rem; }
          h2 { text-align: center; color: #333; }
          .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
          }
          .card {
            background: #ffffff;
            border-left: 6px solid #1976d2;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            padding: 1rem;
            transition: transform .2s, box-shadow .2s;
          }
          .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
          }
          .card h3 {
            margin: 0 0 .5rem;
            color: #1976d2;
            font-size: 1.2rem;
          }
          .card p {
            margin: .3rem 0;
            color: #555;
            font-size: .95rem;
          }
          .footer { text-align: center; margin-top: 2rem; color: #888; font-size: .9rem; }
        </style>
      </head>
      <body>
        <h2>Pedidos Registrados</h2>
        {% if pedidos %}
        <div class="grid">
          {% for p in pedidos %}
          <div class="card">
            <h3>{{ p.plato }}</h3>
            <p><strong>Mozo:</strong> {{ p.mozo }}</p>
            <p><strong>Mesa:</strong> {{ p.mesa }}</p>
            <p><strong>Precio:</strong> S/ {{ "%.2f"|format(p.precio) }}</p>
            <p><strong>Comentario:</strong> {{ p.comentario }}</p>
            <p><strong>Fecha:</strong> {{ p.fecha }}</p>
          </div>
          {% endfor %}
        </div>
        {% else %}
          <p style="text-align:center; color:#666; margin-top:2rem;">No hay pedidos registrados.</p>
        {% endif %}
        <div class="footer">Actualizado al cargar la página.</div>
      </body>
    </html>
    """
    return render_template_string(html, pedidos=pedidos)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
