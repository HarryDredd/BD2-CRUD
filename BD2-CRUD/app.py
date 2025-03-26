from flask import Flask, render_template, request, redirect, url_for, flash
import oracledb
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# ======================================
# Configuración de la conexión a Oracle
# ======================================
def setup_oracle_client():
    """Configura Oracle Instant Client"""
    client_path = r"C:\oracle\instantclient_19_19"
    if Path(client_path).exists():
        os.environ["PATH"] = client_path + ";" + os.environ["PATH"]
        return True
    return False

def verify_connection():
    """Verifica la conexión al iniciar la app"""
    try:
        # Intenta modo thick primero
        try:
            oracledb.init_oracle_client()
            print("🔵 Modo thick activado")
        except:
            print("🟡 Modo thin activado")

        # Prueba de conexión
        conn = oracledb.connect(
            user="HP",
            password="12345",
            dsn="localhost:1521/xe"  # Ajusta según tu configuración
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT '✅ Conexión exitosa a BD2' FROM DUAL")
            print(cursor.fetchone()[0])
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        flash(f"No se pudo conectar a la base de datos: {e}", "danger")
        return False

# ======================================
# Configuración inicial
# ======================================
if not setup_oracle_client():
    print("⚠️ Oracle Instant Client no encontrado. Intentando modo thin...")

if not verify_connection():
    print("⚠️ La aplicación puede no funcionar correctamente")

# ======================================
# Rutas CRUD para TERCEROS
# ======================================
@app.route('/')
def index():
    try:
        with oracledb.connect(user="HP", password="12345", dsn="localhost:1521/xe") as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT TERC_ID, TERC_TIPO_DOC, TERC_NRO_DOC, TERC_NOMBRES, 
                           TERC_APELLIDOS, TO_CHAR(TERC_FECHA_NAC, 'DD/MM/YYYY'), 
                           TERC_TEL, TERC_CORREO, TERC_DIREC, TERC_TIPO, TERC_ESTADO
                    FROM TERCEROS
                    ORDER BY TERC_ID
                """)
                terceros = cursor.fetchall()
        return render_template("index.html", terceros=terceros)
    except Exception as e:
        flash(f"Error al cargar datos: {str(e)}", "danger")
        return render_template("index.html", terceros=[])

@app.route('/form', defaults={'id': None})
@app.route('/form/<int:id>')
def form(id):
    tercero = None
    if id:
        try:
            with oracledb.connect(user="HP", password="12345", dsn="localhost:1521/xe") as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM TERCEROS 
                        WHERE TERC_ID = :id
                    """, {"id": id})
                    tercero = cursor.fetchone()
        except Exception as e:
            flash(f"Error al cargar datos: {str(e)}", "danger")
    return render_template("form.html", tercero=tercero)

@app.route('/save', methods=['POST'])
def save():
    data = request.form.to_dict()
    try:
        with oracledb.connect(user="HP", password="12345", dsn="localhost:1521/xe") as conn:
            with conn.cursor() as cursor:
                if data['id']:  # Actualización
                    cursor.execute("""
                        UPDATE TERCEROS SET
                            TERC_TIPO_DOC = :1,
                            TERC_NRO_DOC = :2,
                            TERC_NOMBRES = :3,
                            TERC_APELLIDOS = :4,
                            TERC_FECHA_NAC = TO_DATE(:5, 'YYYY-MM-DD'),
                            TERC_TEL = :6,
                            TERC_CORREO = :7,
                            TERC_DIREC = :8,
                            TERC_TIPO = :9,
                            TERC_ESTADO = :10
                        WHERE TERC_ID = :11
                    """, [
                        data['tipo_doc'], data['nro_doc'], data['nombres'],
                        data['apellidos'], data['fecha_nac'], data['tel'],
                        data['correo'], data['direc'], data['tipo'],
                        data['estado'], data['id']
                    ])
                else:  # Inserción
                    cursor.execute("SELECT COALESCE(MAX(TERC_ID), 0) + 1 FROM TERCEROS")
                    new_id = cursor.fetchone()[0]
                    cursor.execute("""
                        INSERT INTO TERCEROS VALUES (
                            :1, :2, :3, :4, :5, 
                            TO_DATE(:6, 'YYYY-MM-DD'), :7, :8, :9, :10, :11
                        )
                    """, [
                        new_id, data['tipo_doc'], data['nro_doc'], data['nombres'],
                        data['apellidos'], data['fecha_nac'], data['tel'],
                        data['correo'], data['direc'], data['tipo'], data['estado']
                    ])
                conn.commit()
        flash("¡Registro guardado exitosamente!", "success")
    except Exception as e:
        flash(f"Error al guardar: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    try:
        with oracledb.connect(user="HP", password="12345", dsn="localhost:1521/xe") as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM TERCEROS WHERE TERC_ID = :id", {"id": id})
                conn.commit()
        flash("¡Registro eliminado exitosamente!", "success")
    except Exception as e:
        flash(f"Error al eliminar: {str(e)}", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)