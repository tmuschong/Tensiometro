from flask import Flask, request, render_template_string, jsonify, send_file
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# Variable global para almacenar los datos más recientes
datos_esp = {
    "sistolica": [],
    "diastolica": [],
    "ppm": [],
    "hora": [],
    "minutos": [],
    "segundos": [],
    "dia": [],
    "mes": [],
    "ano": []
}

# Función para generar gráfico y retornar en base64
def generar_grafico(titulo, valores, horas=None, minutos=None):
    fig, ax = plt.subplots(figsize=(10, 3))

    # Si se pasan horas/minutos, construir etiquetas de tiempo
    if horas and minutos and len(horas) == len(valores):
        etiquetas_tiempo = [f"{h:02d}:{m:02d}" for h, m in zip(horas, minutos)]
        ax.plot(etiquetas_tiempo, valores, marker='o')
        ax.set_xlabel("Hora de medición")
    else:
        ax.plot(valores, marker='o')
        ax.set_xlabel("Muestra")

    # Etiquetas de eje Y dinámicas según el tipo de gráfico
    if "Sistólica" in titulo:
        ax.set_ylabel("Presión Sistólica (mmHg)")
    elif "Diastólica" in titulo:
        ax.set_ylabel("Presión Diastólica (mmHg)")
    elif "PPM" in titulo:
        ax.set_ylabel("Pulsaciones por Minuto")
    else:
        ax.set_ylabel("Valor")

    ax.set_title(titulo)
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


# Endpoint POST: recibir datos desde ESP01
@app.route("/data", methods=["POST"])
def recibir_datos():
    global datos_esp
    try:
        contenido = request.get_json()
        for key in datos_esp.keys():
            datos_esp[key] = contenido.get(key, [])
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 400

# Endpoint GET: ver datos en navegador (debug)
@app.route("/data_get", methods=["GET"])
def ver_datos():
    return jsonify(datos_esp)

# Página principal con formulario
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Obtener mediciones ESP
        sistolica = datos_esp.get("sistolica", [])
        diastolica = datos_esp.get("diastolica", [])
        ppm = datos_esp.get("ppm", [])
        # Calcular PP y DP
        pp = []
        dp = []
        for i in range(len(sistolica)):
            if i < len(diastolica) and i < len(ppm):
                pp.append(sistolica[i] - diastolica[i])       # Presión de Pulso
                dp.append(sistolica[i] * ppm[i])              # Doble Producto
            else:
                pp.append(0)
                dp.append(0)

        hora = datos_esp.get("hora", [])
        minutos = datos_esp.get("minutos", [])
        dia = datos_esp.get("dia", [])
        mes = datos_esp.get("mes", [])
        ano = datos_esp.get("ano", [])

        img_sis = generar_grafico("Presión Sistólica", sistolica, hora, minutos)
        img_dia = generar_grafico("Presión Diastólica", diastolica, hora, minutos)
        img_ppm = generar_grafico("PPM", ppm, hora, minutos)


        # Crear filas para la tabla HTML (hora sin segundos y columna separada)
        filas = ""
        for i in range(len(sistolica)):
            hora_str = f"{hora[i]:02d}:{minutos[i]:02d}"
            fecha_str = f"{dia[i]:02d}/{mes[i]:02d}/{ano[i]}"
            filas += f"<tr><td>{i+1}</td><td>{sistolica[i]}</td><td>{diastolica[i]}</td><td>{ppm[i]}</td><td>{pp[i]}</td><td>{dp[i]}</td><td>{hora_str}</td><td>{fecha_str}</td></tr>"

        # Calcular promedios
        if len(sistolica) > 0:
            prom_sis = round(sum(sistolica) / len(sistolica), 1)
            prom_dia = round(sum(diastolica) / len(diastolica), 1)
            prom_ppm = round(sum(ppm) / len(ppm), 1)
            prom_pp = round(sum(pp) / len(pp), 1)
            prom_dp = round(sum(dp) / len(dp), 1)
            filas += f"<tr style='font-weight:bold; background-color:#f2f2f2;'><td>Promedio</td><td>{prom_sis}</td><td>{prom_dia}</td><td>{prom_ppm}</td><td>{prom_pp}</td><td>{prom_dp}</td><td>-</td><td>-</td></tr>"


        html = f"""
        <html>
        <head>
            <title>Informe de Presión</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .datos {{ font-size: 0.9em; text-align: left; margin-bottom: 20px; }}
                .graficos {{ display: flex; flex-direction: column; align-items: center; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    border: 1px solid #ccc;
                    padding: 6px;
                    text-align: center;
                }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="datos">
                <strong>Datos del paciente:</strong><br>
                Nombre: {nombre}<br>
                Apellido: {apellido}<br>
                DNI: {dni}<br>
                Edad: {edad}<br>
                Tiempo de muestreo (min): {tiempo}
            </div>

            <div class="graficos">
                <img src="data:image/png;base64,{img_sis}">
                <img src="data:image/png;base64,{img_dia}">
                <img src="data:image/png;base64,{img_ppm}">
            </div>

            <table>
                <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th><th>PPM</th><th>PP (S-D)</th><th>DP (S×PPM)</th><th>Hora</th><th>Fecha</th></tr>
                {filas}
            </table>

            <br>
            <form action="/exportar_pdf" method="post">
                <input type="hidden" name="nombre" value="{nombre}">
                <input type="hidden" name="apellido" value="{apellido}">
                <input type="hidden" name="dni" value="{dni}">
                <input type="hidden" name="edad" value="{edad}">
                <input type="hidden" name="tiempo" value="{tiempo}">
                <input type="hidden" name="sistolica" value="{','.join(map(str, sistolica))}">
                <input type="hidden" name="diastolica" value="{','.join(map(str, diastolica))}">
                <input type="hidden" name="ppm" value="{','.join(map(str, ppm))}">
                <input type="hidden" name="hora" value="{','.join(map(str, hora))}">
                <input type="hidden" name="minutos" value="{','.join(map(str, minutos))}">
                <input type="hidden" name="dia" value="{','.join(map(str, dia))}">
                <input type="hidden" name="mes" value="{','.join(map(str, mes))}">
                <input type="hidden" name="ano" value="{','.join(map(str, ano))}">
                <input type="hidden" name="img_sis" value="{img_sis}">
                <input type="hidden" name="img_dia" value="{img_dia}">
                <input type="hidden" name="img_ppm" value="{img_ppm}">
                <button type="submit">Exportar a PDF</button>
            </form>
        </body>
        </html>
        """
        return html

    # GET: mostrar formulario
    return """
    <html>
    <head>
        <title>Datos del Paciente</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            form { max-width: 400px; }
            label { display: block; margin-top: 10px; }
            input[type="text"], input[type="number"] {
                width: 100%;
                padding: 6px;
                margin-top: 4px;
            }
            input[type="submit"] {
                margin-top: 20px;
                padding: 10px 20px;
            }
        </style>
    </head>
    <body>
        <h2>Ingresar datos del paciente</h2>
        <form method="POST">
            <label>Nombre:
                <input type="text" name="nombre" required>
            </label>
            <label>Apellido:
                <input type="text" name="apellido" required>
            </label>
            <label>DNI:
                <input type="text" name="dni" required>
            </label>
            <label>Edad:
                <input type="number" name="edad" required>
            </label>
            <label>Tiempo de muestreo (min):
                <input type="number" name="tiempo" required>
            </label>
            <input type="submit" value="Ingresar datos del paciente">
        </form>
    </body>
    </html>
    """

# Exportar PDF
@app.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    # Leer datos del formulario
    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    dni = request.form.get("dni")
    edad = request.form.get("edad")
    tiempo = request.form.get("tiempo")

    sistolica = list(map(int, request.form.get("sistolica").split(',')))
    diastolica = list(map(int, request.form.get("diastolica").split(',')))
    ppm = list(map(int, request.form.get("ppm").split(',')))
    hora = list(map(int, request.form.get("hora").split(',')))
    minutos = list(map(int, request.form.get("minutos").split(',')))
    dia = list(map(int, request.form.get("dia").split(',')))
    mes = list(map(int, request.form.get("mes").split(',')))
    ano = list(map(int, request.form.get("ano").split(',')))

    img_sis_b64 = request.form.get("img_sis")
    img_dia_b64 = request.form.get("img_dia")
    img_ppm_b64 = request.form.get("img_ppm")

    # Guardar imágenes temporales
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_sis, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_dia, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_ppm:
        f_sis.write(base64.b64decode(img_sis_b64))
        f_dia.write(base64.b64decode(img_dia_b64))
        f_ppm.write(base64.b64decode(img_ppm_b64))
        ruta_sis = f_sis.name
        ruta_dia = f_dia.name
        ruta_ppm = f_ppm.name

    elementos.append(Paragraph("Informe de Presión Arterial", styles['Title']))
    elementos.append(Spacer(1, 12))

    info = f"""
    <b>Nombre:</b> {nombre}<br/>
    <b>Apellido:</b> {apellido}<br/>
    <b>DNI:</b> {dni}<br/>
    <b>Edad:</b> {edad}<br/>
    <b>Tiempo de muestreo:</b> {tiempo} min
    """
    elementos.append(Paragraph(info, styles['Normal']))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Sistólica", styles['Heading2']))
    elementos.append(RLImage(ruta_sis, width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico Presión Diastólica", styles['Heading2']))
    elementos.append(RLImage(ruta_dia, width=400, height=150))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Gráfico PPM", styles['Heading2']))
    elementos.append(RLImage(ruta_ppm, width=400, height=150))
    elementos.append(Spacer(1, 12))

    # Tabla con fecha y hora separadas (sin segundos)
    # Calcular PP y DP también para el PDF
    pp = []
    dp = []
    for i in range(len(sistolica)):
        if i < len(diastolica) and i < len(ppm):
            pp.append(sistolica[i] - diastolica[i])
            dp.append(sistolica[i] * ppm[i])
        else:
            pp.append(0)
            dp.append(0)

    tabla_datos = [["N°", "Sistólica", "Diastólica", "PPM", "PP (S-D)", "DP (S×PPM)", "Hora", "Fecha"]]
        # Tabla con fecha y hora separadas (sin segundos)
    # Calcular PP y DP también para el PDF
    pp = []
    dp = []
    for i in range(len(sistolica)):
        if i < len(diastolica) and i < len(ppm):
            pp.append(sistolica[i] - diastolica[i])
            dp.append(sistolica[i] * ppm[i])
        else:
            pp.append(0)
            dp.append(0)

    # Crear tabla con cabeceras
    tabla_datos = [["N°", "Sistólica", "Diastólica", "PPM", "PP (S-D)", "DP (S×PPM)", "Hora", "Fecha"]]
    for i in range(len(sistolica)):
        hora_str = f"{hora[i]:02d}:{minutos[i]:02d}"
        fecha_str = f"{dia[i]:02d}/{mes[i]:02d}/{ano[i]}"
        tabla_datos.append([
            str(i+1),
            str(sistolica[i]),
            str(diastolica[i]),
            str(ppm[i]),
            str(pp[i]),
            str(dp[i]),
            hora_str,
            fecha_str
        ])

    # Agregar fila de promedios
    if len(sistolica) > 0:
        prom_sis = round(sum(sistolica) / len(sistolica), 1)
        prom_dia = round(sum(diastolica) / len(diastolica), 1)
        prom_ppm = round(sum(ppm) / len(ppm), 1)
        prom_pp = round(sum(pp) / len(pp), 1)
        prom_dp = round(sum(dp) / len(dp), 1)
        tabla_datos.append([
            "Promedio",
            str(prom_sis),
            str(prom_dia),
            str(prom_ppm),
            str(prom_pp),
            str(prom_dp),
            "-",
            "-"
        ])

    # Crear tabla PDF con estilo
    from reportlab.platypus import TableStyle
    from reportlab.lib import colors

    t = Table(tabla_datos, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ]))



    t = Table(tabla_datos, repeatRows=1)
    from reportlab.platypus import TableStyle
    from reportlab.lib import colors

    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))

    elementos.append(t)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)

