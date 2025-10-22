from flask import Flask, request, render_template_string, jsonify, send_file
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import statistics

app = Flask(__name__)

# Variable global para almacenar los datos más recientes
datos_esp = {
    "sistolica": [],
    "diastolica": [],
    "ppm": [],
    "hora": [],
    "minutos": [],
    "pam": [],        # antes 'segundos'
    "dia": [],
    "mes": [],
    "ano": []
}

# Helper: obtener valor seguro (evita IndexError)
def safe_get(lst, i, default=""):
    try:
        return lst[i]
    except Exception:
        return default

# Función para generar gráfico y retornar en base64
def generar_grafico(titulo, valores, horas=None, minutos=None):
    fig, ax = plt.subplots(figsize=(10, 3))
    if horas and minutos and len(horas) == len(valores):
        etiquetas_tiempo = [f"{h:02d}:{m:02d}" for h, m in zip(horas, minutos)]
        ax.plot(etiquetas_tiempo, valores, marker='o')
        ax.set_xlabel("Hora de medición")
    else:
        ax.plot(range(len(valores)), valores, marker='o')
        ax.set_xlabel("Muestra")

    if "Sistólica" in titulo:
        ax.set_ylabel("Presión Sistólica (mmHg)")
    elif "Diastólica" in titulo:
        ax.set_ylabel("Presión Diastólica (mmHg)")
    elif "PPM" in titulo:
        ax.set_ylabel("Pulsaciones por Minuto")
    elif "PAM" in titulo:
        ax.set_ylabel("Presión Arterial Media (mmHg)")
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

# Función para calcular resumen: Max, Min, Media, Desvío
def calcular_resumen(valores):
    if not valores:
        return ["-", "-", "-", "-"]
    try:
        mean_v = round(statistics.mean(valores), 1)
        stdev_v = round(statistics.stdev(valores), 1) if len(valores) > 1 else 0
        return [max(valores), min(valores), mean_v, stdev_v]
    except Exception:
        return ["-", "-", "-", "-"]

# Endpoint POST: recibir datos desde ESP01 (JSON)
@app.route("/data", methods=["POST"])
def recibir_datos():
    global datos_esp
    try:
        contenido = request.get_json()
        for key in datos_esp.keys():
            # si la key no viene, dejamos la lista anterior o la vacía
            datos_esp[key] = contenido.get(key, datos_esp.get(key, []))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 400

# Endpoint GET: ver datos en navegador (debug)
@app.route("/data_get", methods=["GET"])
def ver_datos():
    return jsonify(datos_esp)

# Página principal
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Datos paciente
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Medidas ESP (pueden tener longitudes diferentes)
        sistolica = datos_esp.get("sistolica", [])
        diastolica = datos_esp.get("diastolica", [])
        ppm = datos_esp.get("ppm", [])
        hora = datos_esp.get("hora", [])
        minutos = datos_esp.get("minutos", [])
        pam = datos_esp.get("pam", [])   # ahora PAM
        dia = datos_esp.get("dia", [])
        mes = datos_esp.get("mes", [])
        ano = datos_esp.get("ano", [])

        n = len(sistolica)

        # PP y DP (calcular solo cuando hay datos)
        pp = []
        dp = []
        for i in range(n):
            s = safe_get(sistolica, i, 0)
            d = safe_get(diastolica, i, 0)
            p = safe_get(ppm, i, 0)
            pp.append(s - d if (s != "" and d != "") else "")
            dp.append(s * p if (s != "" and p != "") else "")

        # Graficos
        img_sis = generar_grafico("Presión Sistólica", [safe_get(sistolica,i,0) for i in range(n)], hora, minutos)
        img_dia = generar_grafico("Presión Diastólica", [safe_get(diastolica,i,0) for i in range(n)], hora, minutos)
        img_ppm = generar_grafico("PPM", [safe_get(ppm,i,0) for i in range(n)], hora, minutos)

        # --- Resumen Total / Diurno / Nocturno ---
        indices_diurno = [i for i,h in enumerate(hora) if isinstance(h, (int,float)) and 7 <= h < 22]
        indices_nocturno = [i for i,h in enumerate(hora) if isinstance(h, (int,float)) and (h < 7 or h >= 22)]

        def extraer_lista(indices, lista):
            return [lista[i] for i in indices if i < len(lista)]

        resumen_total = {
            "Sistolica": calcular_resumen([v for v in sistolica if isinstance(v,(int,float))]),
            "Diastolica": calcular_resumen([v for v in diastolica if isinstance(v,(int,float))]),
            "PAM": calcular_resumen([v for v in pam if isinstance(v,(int,float))]),
            "PPM": calcular_resumen([v for v in ppm if isinstance(v,(int,float))]),
            "PP": calcular_resumen([v for v in pp if isinstance(v,(int,float))]),
            "DP": calcular_resumen([v for v in dp if isinstance(v,(int,float))])
        }
        resumen_diurno = {
            "Sistolica": calcular_resumen(extraer_lista(indices_diurno, sistolica)),
            "Diastolica": calcular_resumen(extraer_lista(indices_diurno, diastolica)),
            "PAM": calcular_resumen(extraer_lista(indices_diurno, pam)),
            "PPM": calcular_resumen(extraer_lista(indices_diurno, ppm)),
            "PP": calcular_resumen(extraer_lista(indices_diurno, pp)),
            "DP": calcular_resumen(extraer_lista(indices_diurno, dp))
        }
        resumen_nocturno = {
            "Sistolica": calcular_resumen(extraer_lista(indices_nocturno, sistolica)),
            "Diastolica": calcular_resumen(extraer_lista(indices_nocturno, diastolica)),
            "PAM": calcular_resumen(extraer_lista(indices_nocturno, pam)),
            "PPM": calcular_resumen(extraer_lista(indices_nocturno, ppm)),
            "PP": calcular_resumen(extraer_lista(indices_nocturno, pp)),
            "DP": calcular_resumen(extraer_lista(indices_nocturno, dp))
        }

        def generar_tabla_html(resumen, titulo):
            filas = ""
            for clave, valores in resumen.items():
                filas += f"<tr><td>{clave}</td><td>{valores[0]}</td><td>{valores[1]}</td><td>{valores[2]}</td><td>{valores[3]}</td></tr>"
            return f"""
            <h3>{titulo}</h3>
            <table>
                <tr><th>Variable</th><th>Máx</th><th>Mín</th><th>Media</th><th>Desvío</th></tr>
                {filas}
            </table><br>
            """

        html_resumen = generar_tabla_html(resumen_total, "Total") + generar_tabla_html(resumen_diurno, "Diurno") + generar_tabla_html(resumen_nocturno, "Nocturno")

        # Tabla principal con promedio (manejo seguro de índices)
        filas = ""
        for i in range(n):
            hora_str = f"{safe_get(hora,i,'') :02d}:{safe_get(minutos,i,'') :02d}" if (isinstance(safe_get(hora,i),int) and isinstance(safe_get(minutos,i),int)) else safe_get(hora,i,'')
            fecha_str = f"{safe_get(dia,i,''):02d}/{safe_get(mes,i,''):02d}/{safe_get(ano,i,'')}" if (isinstance(safe_get(dia,i),int) and isinstance(safe_get(mes,i),int) and isinstance(safe_get(ano,i),int)) else ""
            filas += f"<tr><td>{i+1}</td><td>{safe_get(sistolica,i,'')}</td><td>{safe_get(diastolica,i,'')}</td><td>{safe_get(pam,i,'')}</td><td>{safe_get(ppm,i,'')}</td><td>{safe_get(pp,i,'')}</td><td>{safe_get(dp,i,'')}</td><td>{hora_str}</td><td>{fecha_str}</td></tr>"

        # Promedios (si hay datos)
        def mean_or_dash(lst):
            vals = [v for v in lst if isinstance(v,(int,float))]
            return round(sum(vals)/len(vals),1) if vals else "-"

        if n > 0:
            prom_sis = mean_or_dash(sistolica)
            prom_dia = mean_or_dash(diastolica)
            prom_pam = mean_or_dash(pam)
            prom_ppm = mean_or_dash(ppm)
            prom_pp = mean_or_dash(pp)
            prom_dp = mean_or_dash(dp)
            filas += f"<tr style='font-weight:bold; background-color:#f2f2f2;'><td>Promedio</td><td>{prom_sis}</td><td>{prom_dia}</td><td>{prom_pam}</td><td>{prom_ppm}</td><td>{prom_pp}</td><td>{prom_dp}</td><td>-</td><td>-</td></tr>"

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
            <img src="data:image/png;base64,{img_sis}">
            <img src="data:image/png;base64,{img_dia}">
            <img src="data:image/png;base64,{img_ppm}">
        </div>

        {html_resumen}

        <table>
            <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th><th>PAM</th><th>PPM</th><th>PP (S-D)</th><th>DP (S×PPM)</th><th>Hora</th><th>Fecha</th></tr>
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
            <input type="hidden" name="pam" value="{','.join(map(str, pam))}">
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
    <html><head><title>Datos del Paciente</title></head>
    <body>
    <h2>Ingresar datos del paciente</h2>
    <form method="POST">
        Nombre:<input type="text" name="nombre" required><br>
        Apellido:<input type="text" name="apellido" required><br>
        DNI:<input type="text" name="dni" required><br>
        Edad:<input type="number" name="edad" required><br>
        Tiempo de muestreo (min):<input type="number" name="tiempo" required><br>
        <input type="submit" value="Ingresar datos">
    </form>
    </body></html>
    """

# --- Exportar PDF ---
@app.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    # Datos formulario
    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    dni = request.form.get("dni")
    edad = request.form.get("edad")
    tiempo = request.form.get("tiempo")

    # Parsear listas (pam puede ser float)
    sistolica = [float(x) if x!='' else 0 for x in request.form.get("sistolica","").split(',') if x!='']
    diastolica = [float(x) if x!='' else 0 for x in request.form.get("diastolica","").split(',') if x!='']
    pam = [float(x) if x!='' else 0 for x in request.form.get("pam","").split(',') if x!='']
    ppm = [float(x) if x!='' else 0 for x in request.form.get("ppm","").split(',') if x!='']
    hora = [int(x) for x in request.form.get("hora","").split(',') if x!='']
    minutos = [int(x) for x in request.form.get("minutos","").split(',') if x!='']
    dia = [int(x) for x in request.form.get("dia","").split(',') if x!='']
    mes = [int(x) for x in request.form.get("mes","").split(',') if x!='']
    ano = [int(x) for x in request.form.get("ano","").split(',') if x!='']

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
    elementos.append(Spacer(1,12))

    info = f"<b>Nombre:</b> {nombre}<br/><b>Apellido:</b> {apellido}<br/><b>DNI:</b> {dni}<br/><b>Edad:</b> {edad}<br/><b>Tiempo de muestreo:</b> {tiempo} min"
    elementos.append(Paragraph(info, styles['Normal']))
    elementos.append(Spacer(1,12))

    elementos.append(Paragraph("Gráfico Presión Sistólica", styles['Heading2']))
    elementos.append(RLImage(ruta_sis, width=400, height=150))
    elementos.append(Spacer(1,12))

    elementos.append(Paragraph("Gráfico Presión Diastólica", styles['Heading2']))
    elementos.append(RLImage(ruta_dia, width=400, height=150))
    elementos.append(Spacer(1,12))

    elementos.append(Paragraph("Gráfico PPM", styles['Heading2']))
    elementos.append(RLImage(ruta_ppm, width=400, height=150))
    elementos.append(Spacer(1,12))

    # --- Resumen Total / Diurno / Nocturno para PDF ---
    indices_diurno = [i for i,h in enumerate(hora) if 7 <= h < 22]
    indices_nocturno = [i for i,h in enumerate(hora) if h < 7 or h >= 22]
    def extraer_lista(indices, lista):
        return [lista[i] for i in indices if i < len(lista)]

    pp = [s-d for s,d in zip(sistolica, diastolica)]
    dp = [s*p for s,p in zip(sistolica, ppm)]

    resumen_total = {
        "Sistolica": calcular_resumen(sistolica),
        "Diastolica": calcular_resumen(diastolica),
        "PAM": calcular_resumen(pam),
        "PPM": calcular_resumen(ppm),
        "PP": calcular_resumen(pp),
        "DP": calcular_resumen(dp)
    }
    resumen_diurno = {
        "Sistolica": calcular_resumen(extraer_lista(indices_diurno, sistolica)),
        "Diastolica": calcular_resumen(extraer_lista(indices_diurno, diastolica)),
        "PAM": calcular_resumen(extraer_lista(indices_diurno, pam)),
        "PPM": calcular_resumen(extraer_lista(indices_diurno, ppm)),
        "PP": calcular_resumen(extraer_lista(indices_diurno, pp)),
        "DP": calcular_resumen(extraer_lista(indices_diurno, dp))
    }
    resumen_nocturno = {
        "Sistolica": calcular_resumen(extraer_lista(indices_nocturno, sistolica)),
        "Diastolica": calcular_resumen(extraer_lista(indices_nocturno, diastolica)),
        "PAM": calcular_resumen(extraer_lista(indices_nocturno, pam)),
        "PPM": calcular_resumen(extraer_lista(indices_nocturno, ppm)),
        "PP": calcular_resumen(extraer_lista(indices_nocturno, pp)),
        "DP": calcular_resumen(extraer_lista(indices_nocturno, dp))
    }

    def generar_tabla_pdf(resumen, titulo):
        elementos_tabla = [[titulo,"Máx","Mín","Media","Desvío"]]
        for k,v in resumen.items():
            elementos_tabla.append([k]+v)
        t = Table(elementos_tabla, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')
        ]))
        return t

    elementos.append(generar_tabla_pdf(resumen_total,"Total"))
    elementos.append(Spacer(1,12))
    elementos.append(generar_tabla_pdf(resumen_diurno,"Diurno"))
    elementos.append(Spacer(1,12))
    elementos.append(generar_tabla_pdf(resumen_nocturno,"Nocturno"))
    elementos.append(Spacer(1,12))

    # Tabla principal PDF
    tabla_datos = [["N°","Sistólica","Diastólica","PAM","PPM","PP (S-D)","DP (S×PPM)","Hora","Fecha"]]
    for i in range(len(sistolica)):
        hora_str = f"{hora[i]:02d}:{minutos[i]:02d}" if i < len(hora) and i < len(minutos) else ""
        fecha_str = f"{dia[i]:02d}/{mes[i]:02d}/{ano[i]}" if i < len(dia) and i < len(mes) and i < len(ano) else ""
        tabla_datos.append([str(i+1), str(sistolica[i]), str(diastolica[i]), str(pam[i]) if i < len(pam) else "", str(ppm[i]) if i < len(ppm) else "", str(pp[i]) if i < len(pp) else "", str(dp[i]) if i < len(dp) else "", hora_str, fecha_str])

    # Agregar fila de promedios (si hay datos)
    def mean_str(lst):
        vals = [v for v in lst if isinstance(v,(int,float))]
        return str(round(statistics.mean(vals),1)) if vals else "-"

    tabla_datos.append(["Promedio",
                       mean_str(sistolica),
                       mean_str(diastolica),
                       mean_str(pam),
                       mean_str(ppm),
                       mean_str(pp),
                       mean_str(dp),
                       "-","-"])

    t_principal = Table(tabla_datos, repeatRows=1)
    t_principal.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('BACKGROUND',(0,-1),(-1,-1),colors.whitesmoke),
        ('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold')
    ]))
    elementos.append(t_principal)

    doc.build(elementos)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="informe_presion.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)
