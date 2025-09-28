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
    "hora": [],
    "minutos": [],
    "segundos": [],
    "dia": [],
    "mes": [],
    "ano": [],
    "ppm": []
}

def generar_grafico(titulo, valores):
    if not valores:
        valores = [0]
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Valor")
    ax.set_xlabel("Muestra")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# Endpoint para recibir datos desde ESP01
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

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Datos del paciente
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Tomar datos ESP01
        s = datos_esp.get("sistolica", [])
        d = datos_esp.get("diastolica", [])
        h = datos_esp.get("hora", [])
        m = datos_esp.get("minutos", [])
        seg = datos_esp.get("segundos", [])
        dia = datos_esp.get("dia", [])
        mes = datos_esp.get("mes", [])
        ano = datos_esp.get("ano", [])
        ppm = datos_esp.get("ppm", [])

        img_sis = generar_grafico("Presión Sistólica", s)
        img_dia = generar_grafico("Presión Diastólica", d)
        img_ppm = generar_grafico("Pulso (ppm)", ppm)

        # Determinar longitud mínima para zip
        longitud = min(len(s), len(d), len(h), len(m), len(seg), len(dia), len(mes), len(ano), len(ppm))
        filas = ""
        for i in range(longitud):
            filas += f"<tr><td>{i+1}</td><td>{s[i]}</td><td>{d[i]}</td>"
            filas += f"<td>{h[i]:02d}:{m[i]:02d}:{seg[i]:02d}</td>"
            filas += f"<td>{dia[i]}/{mes[i]}/{2000+ano[i]}</td>"
            filas += f"<td>{ppm[i]}</td></tr>"

        html = f"""
        <html>
        <head>
            <title>Informe de Presión</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                .datos {{ font-size: 0.9em; text-align: left; margin-bottom: 20px; }}
                .graficos {{ display: flex; flex-direction: column; align-items: center; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ccc; padding: 6px; text-align: center; }}
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
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{img_sis}">
                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{img_dia}">
                <h2>Pulso (ppm)</h2>
                <img src="data:image/png;base64,{img_ppm}">
            </div>

            <table>
                <tr>
                    <th>N°</th>
                    <th>Sistólica</th>
                    <th>Diastólica</th>
                    <th>Hora</th>
                    <th>Fecha</th>
                    <th>Pulso (ppm)</th>
                </tr>
                {filas}
            </table>

            <br>
            <form action="/exportar_pdf" method="post">
                <input type="hidden" name="nombre" value="{nombre}">
                <input type="hidden" name="apellido" value="{apellido}">
                <input type="hidden" name="dni" value="{dni}">
                <input type="hidden" name="edad" value="{edad}">
                <input type="hidden" name="tiempo" value="{tiempo}">
                <input type="hidden" name="sistolica" value="{','.join(map(str, s))}">
                <input type="hidden" name="diastolica" value="{','.join(map(str, d))}">
                <input type="hidden" name="hora" value="{','.join(map(str, h))}">
                <input type="hidden" name="minutos" value="{','.join(map(str, m))}">
                <input type="hidden" name="segundos" value="{','.join(map(str, seg))}">
                <input type="hidden" name="dia" value="{','.join(map(str, dia))}">
                <input type="hidden" name="mes" value="{','.join(map(str, mes))}">
                <input type="hidden" name="ano" value="{','.join(map(str, ano))}">
                <input type="hidden" name="ppm" value="{','.join(map(str, ppm))}">
                <input type="hidden" name="img_sis" value="{img_sis}">
                <input type="hidden" name="img_dia" value="{img_dia}">
                <input type="hidden" name="img_ppm" value="{img_ppm}">
                <button type="submit">Exportar a PDF</button>
            </form>
        </body>
        </html>
        """
        return html

    # GET: formulario
    return """
    <html>
    <head>
        <title>Datos del Paciente</title>
        <style>
            body { font-family: Arial; margin: 40px; }
            form { max-width: 400px; }
            label { display: block; margin-top: 10px; }
            input[type="text"], input[type="number"] { width: 100%; padding: 6px; margin-top: 4px; }
            input[type="submit"] { margin-top: 20px; padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h2>Ingresar datos del paciente</h2>
        <form method="POST">
            <label>Nombre:<input type="text" name="nombre" required></label>
            <label>Apellido:<input type="text" name="apellido" required></label>
            <label>DNI:<input type="text" name="dni" required></label>
            <label>Edad:<input type="number" name="edad" required></label>
            <label>Tiempo de muestreo (min):<input type="number" name="tiempo" required></label>
            <input type="submit" value="Ingresar datos del paciente">
        </form>
    </body>
    </html>
    """

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

    campos = ["sistolica", "diastolica", "hora", "minutos", "segundos", "dia", "mes", "ano", "ppm"]
    datos = {}
    for campo in campos:
        valor = request.form.get(campo, "")
        if valor:
            datos[campo] = list(map(int, valor.split(',')))
        else:
            datos[campo] = []

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

    elementos.append(Paragraph("Gráfico Pulso (ppm)", styles['Heading2']))
    elementos.append(RLImage(ruta_ppm, width=400, height=150))
    elementos.append(Spacer(1, 12))

    # Tabla completa con hora, fecha y ppm
    longitud = min(len(datos["sistolica"]), len(datos["diastolica"]), len(datos["hora"]), len(datos["minutos"]),
                   len(datos["segundos"]), len(datos["dia"]), len(datos["mes"]), len(datos["ano"]), len(datos["ppm"]))
    tabla_datos = [["N°", "Sistólica", "Diastólica", "Hora", "Fecha", "Pulso (ppm)"]]
    for i in range(longitud):
        tabla_datos.append([
            str(i+1),
            str(datos["sistolica"][i]),
            str(datos["diastolica"][i]),
            f"{datos['hora'][i]:02d}:{datos['minutos'][i]:02d}:{datos['segundos'][i]:02d}",
            f"{datos['dia'][i]}/{datos['mes'][i]}/{2000+datos['ano'][i]}",
            str(datos["ppm"][i])
        ])

    t = Table(tabla_datos, repeatRows=1)
    elementos.append(t)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)
