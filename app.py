import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder='templates')

def cargar_env_local(path='.env'):
    if not os.path.exists(path):
        return

    with open(path, encoding='utf-8') as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith('#') or '=' not in linea:
                continue

            clave, valor = linea.split('=', 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            os.environ.setdefault(clave, valor)


cargar_env_local()

# Configuración de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_SSLMODE = os.getenv('DB_SSLMODE', 'require')


def conectar_db():
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL)

        if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
            raise RuntimeError(
                'Faltan variables de entorno de base de datos. Define DATABASE_URL o DB_HOST, DB_NAME, DB_USER y DB_PASSWORD.'
            )

        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            sslmode=DB_SSLMODE,
        )
    except (psycopg2.Error, RuntimeError) as e:
        print("Error al conectar a la base de datos:", e)
        return None


def crear_tabla_personas():
    conn = conectar_db()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id SERIAL PRIMARY KEY,
                dni VARCHAR(20) NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                apellido VARCHAR(100) NOT NULL,
                direccion TEXT,
                telefono VARCHAR(20)
            );
        """)
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print("Error al crear la tabla personas:", e)
    finally:
        conn.close()


def crear_persona(dni, nombre, apellido, direccion, telefono):
    conn = conectar_db()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO personas (dni, nombre, apellido, direccion, telefono) VALUES (%s, %s, %s, %s, %s)",
                       (dni, nombre, apellido, direccion, telefono))
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print("Error al crear la persona:", e)
    finally:
        conn.close()

def obtener_registros():
    conn = conectar_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personas order by apellido")
        return cursor.fetchall()
    except psycopg2.Error as e:
        print("Error al obtener registros:", e)
        return []
    finally:
        conn.close()


crear_tabla_personas()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    dni = request.form['dni']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    crear_persona(dni, nombre, apellido, direccion, telefono)
    mensaje_confirmacion = "Registro Exitoso"
    return redirect(url_for('index', mensaje_confirmacion=mensaje_confirmacion))

@app.route('/administrar')
def administrar():
    registros = obtener_registros()
    return render_template('administrar.html', registros=registros)

@app.route('/eliminar/<int:persona_id>', methods=['POST'])
def eliminar_registro(persona_id):
    conn = conectar_db()
    if conn is None:
        return redirect(url_for('administrar'))

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print("Error al eliminar el registro:", e)
    finally:
        conn.close()

    return redirect(url_for('administrar'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)