from flask import Flask, request, jsonify, send_file
import matplotlib.pyplot as plt
import io
import base64
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import statistics
import math

app = Flask(__name__)

# Variable global para almacenar los datos más recientes
datos_esp = {
    "sistolica": [],
    "diastolica": [],
    "ppm": [],
    "hora": [],
    "minutos": [],
    "pam": [],        
    "dia": [],
    "mes": [],
    "ano": []
}

# Helper: obtener valor seguro (evita IndexError)
def safe_get(lst, i, default=None):
    try:
        return lst[i]
    except Exception:
        return default

# convierte lista de valores a floats cuando sea posible
def to_numeric_list(lst):
    res = []
    for v in lst:
        try:
            res.append(float(v))
        except Exception:
            pass
    return res

# Genera gráfico combinado
def generar_grafico_combinado(sistolica, diastolica, ppm, pam, hora=None, minutos=None):
    n = max(len(sistolica), len(diastolica), len(ppm), len(pam))

    def v_at(lst, i):
        try:
            return float(lst[i])
        except Exception:
            return math.nan

    y_sis = [v_at(sistolica, i) for i in range(n)]
    y_dia = [v_at(diastolica, i) for i in range(n)]
    y_ppm = [v_at(ppm, i) for i in range(n)]
    y_pam = [v_at(pam, i) for i in range(n)]

    if hora and minutos and len(hora) >= n and len(minutos) >= n:
        etiquetas = [f"{int(hora[i]):02d}:{int(minutos[i]):02d}" for i in range(n)]
        x = list(range(n))
        xticks = x
        xticklabels = etiquetas
    else:
        x = list(range(n))
        xticks = x
        xticklabels = [str(i+1) for i in x]

    fig, ax = plt.subplots(figsize=(10, 4))

    # ✅ Líneas con colores y estilos más distinguibles
    ax.plot(x, y_sis, marker='o', color='red', label='Sistólica (mmHg)', linewidth=2)
    ax.plot(x, y_dia, marker='o', color='blue', label='Diastólica (mmHg)', linewidth=2)
    ax.scatter(x, y_ppm, label='PPM', color='green', marker='x', s=60)
    ax.scatter(x, y_pam, label='PAM', color='purple', marker='s', s=50)

    ax.set_xlabel("Hora de medición" if hora and minutos else "Muestra")
    ax.set_ylabel("Valor (mmHg / PPM)")
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=45)
    ax.set_ylim(bottom=0)  # ✅ Eje Y comienza en 0

    # ✅ Cuadrícula gris suave
    ax.grid(True, linestyle='--', color='lightgrey', alpha=0.6)

    # ✅ Leyenda arriba y centrada
    ax.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, 1.25),
        ncol=2,
        frameon=False,
        fontsize=9
    )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')



# Función para calcular resumen: Max, Min, Media, Desvío
def calcular_resumen(valores):
    vals = [v for v in valores if isinstance(v, (int, float))]
    if len(vals) == 0:
        return ["-", "-", "-", "-"]
    m = round(statistics.mean(vals), 1)
    sd = round(statistics.stdev(vals), 1) if len(vals) > 1 else 0
    return [max(vals), min(vals), m, sd]

# Endpoint POST: recibir datos desde ESP01 (JSON)
@app.route('/data', methods=['POST'])
def recibir_datos():
    global datos_esp
    try:
        data = request.get_json()

        # ✅ Reemplaza completamente los datos anteriores
        datos_esp = {
            'sistolica': data.get('sistolica', []),
            'diastolica': data.get('diastolica', []),
            'pam': data.get('pam', []),
            'ppm': data.get('ppm', []),
            'hora': data.get('hora', []),
            'minutos': data.get('minutos', []),
            'dia': data.get('dia', []),
            'mes': data.get('mes', []),
            'ano': data.get('ano', [])
        }

        print(f"[Flask] Datos recibidos ({len(datos_esp['sistolica'])} muestras)")
        return jsonify({"status": "ok", "mensaje": "Datos reemplazados correctamente"}), 200

    except Exception as e:
        print(f"[Error] {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 400


# Endpoint GET: ver datos en navegador (debug)
@app.route("/data_get", methods=["GET"])
def ver_datos():
    return jsonify(datos_esp)

# Página principal (form + muestra)
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        sistolica = datos_esp.get("sistolica", [])
        diastolica = datos_esp.get("diastolica", [])
        ppm = datos_esp.get("ppm", [])
        hora = datos_esp.get("hora", [])
        minutos = datos_esp.get("minutos", [])
        pam = datos_esp.get("pam", [])
        dia = datos_esp.get("dia", [])
        mes = datos_esp.get("mes", [])
        ano = datos_esp.get("ano", [])

        n = max(len(sistolica), len(diastolica), len(ppm), len(pam))
        pp = []
        dp = []
        for i in range(n):
            s = safe_get(sistolica, i, None)
            d = safe_get(diastolica, i, None)
            p = safe_get(ppm, i, None)
            try: s_f = float(s)
            except: s_f = None
            try: d_f = float(d)
            except: d_f = None
            try: p_f = float(p)
            except: p_f = None
            pp.append(s_f - d_f if (s_f is not None and d_f is not None) else None)
            dp.append(s_f * p_f if (s_f is not None and p_f is not None) else None)

        img_comb = generar_grafico_combinado(sistolica, diastolica, ppm, pam, hora, minutos)

        indices_diurno = [i for i,h in enumerate(hora) if isinstance(h, (int,float)) and 7 <= h < 22]
        indices_nocturno = [i for i,h in enumerate(hora) if isinstance(h, (int,float)) and (h < 7 or h >= 22)]
        def extraer_lista(indices, lista):
            return [lista[i] for i in indices if i < len(lista) and isinstance(lista[i], (int,float))]

        resumen_total = {
            "Sistolica": calcular_resumen([v for v in sistolica if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace('.','',1).isdigit() )]),
            "Diastolica": calcular_resumen([v for v in diastolica if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace('.','',1).isdigit() )]),
            "PAM": calcular_resumen([v for v in pam if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace('.','',1).isdigit() )]),
            "PPM": calcular_resumen([v for v in ppm if isinstance(v,(int,float)) or (isinstance(v,str) and v.replace('.','',1).isdigit() )]),
            "PP": calcular_resumen([v for v in pp if isinstance(v,(int,float))]),
            "DP": calcular_resumen([v for v in dp if isinstance(v,(int,float))])
        }
        resumen_diurno = {k: calcular_resumen(extraer_lista(indices_diurno, v)) for k,v in zip(resumen_total.keys(), [sistolica, diastolica, pam, ppm, pp, dp])}
        resumen_nocturno = {k: calcular_resumen(extraer_lista(indices_nocturno, v)) for k,v in zip(resumen_total.keys(), [sistolica, diastolica, pam, ppm, pp, dp])}

        def generar_tabla_html(resumen, titulo):
            filas = ""
            for clave, valores in resumen.items():
                filas += f"<tr><td>{clave}</td><td>{valores[0]}</td><td>{valores[1]}</td><td>{valores[2]}</td><td>{valores[3]}</td></tr>"
            return f"<h3>{titulo}</h3><table><tr><th>Variable</th><th>Máx</th><th>Mín</th><th>Media</th><th>Desvío</th></tr>{filas}</table><br>"

        html_resumen = generar_tabla_html(resumen_total, "Total") + generar_tabla_html(resumen_diurno, "Diurno") + generar_tabla_html(resumen_nocturno, "Nocturno")

        filas = ""
        for i in range(n):
            hora_str = f"{int(hora[i]):02d}:{int(minutos[i]):02d}" if (i < len(hora) and i < len(minutos) and isinstance(hora[i], (int,float)) and isinstance(minutos[i], (int,float))) else (safe_get(hora,i,""))
            fecha_str = f"{int(dia[i]):02d}/{int(mes[i]):02d}/{int(ano[i])}" if (i < len(dia) and i < len(mes) and i < len(ano) and isinstance(dia[i], (int,float)) and isinstance(mes[i], (int,float)) and isinstance(ano[i], (int,float))) else ""
            filas += f"<tr><td>{i+1}</td><td>{safe_get(sistolica,i,'')}</td><td>{safe_get(diastolica,i,'')}</td><td>{safe_get(pam,i,'')}</td><td>{safe_get(ppm,i,'')}</td><td>{safe_get(pp,i,'')}</td><td>{safe_get(dp,i,'')}</td><td>{hora_str}</td><td>{fecha_str}</td></tr>"

        def mean_or_dash(lst):
            vals = []
            for v in lst:
                try:
                    if isinstance(v,(int,float)):
                        vals.append(v)
                    else:
                        vals.append(float(v))
                except Exception:
                    pass
            return round(sum(vals)/len(vals),1) if vals else "-"

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
            <h2>Gráfico de Tendencias</h2>
            <img src="data:image/png;base64,{img_comb}">
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
            <input type="hidden" name="img_comb" value="{img_comb}">
            <button type="submit">Exportar a PDF</button>
        </form>
        </body>
        </html>
        """
        return html

    # GET muestra formulario
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

# Exportar PDF
@app.route("/exportar_pdf", methods=["POST"])
def exportar_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    dni = request.form.get("dni")
    edad = request.form.get("edad")
    tiempo = request.form.get("tiempo")

    def parse_floats(s):
        if not s:
            return []
        return [float(x) for x in s.split(',') if x != '']

    def parse_ints(s):
        if not s:
            return []
        return [int(x) for x in s.split(',') if x != '']

    sistolica = parse_floats(request.form.get("sistolica",""))
    diastolica = parse_floats(request.form.get("diastolica",""))
    pam = parse_floats(request.form.get("pam",""))
    ppm = parse_floats(request.form.get("ppm",""))
    hora = parse_ints(request.form.get("hora",""))
    minutos = parse_ints(request.form.get("minutos",""))
    dia = parse_ints(request.form.get("dia",""))
    mes = parse_ints(request.form.get("mes",""))
    ano = parse_ints(request.form.get("ano",""))

    img_comb_b64 = request.form.get("img_comb","")

    if img_comb_b64:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_comb:
            f_comb.write(base64.b64decode(img_comb_b64))
            ruta_comb = f_comb.name
    else:
        ruta_comb = None

    elementos.append(Paragraph("Informe de Presión Arterial", styles['Title']))
    elementos.append(Spacer(1,12))
    info = f"<b>Nombre:</b> {nombre}<br/><b>Apellido:</b> {apellido}<br/><b>DNI:</b> {dni}<br/><b>Edad:</b> {edad}<br/><b>Tiempo de muestreo:</b> {tiempo} min"
    elementos.append(Paragraph(info, styles['Normal']))
    elementos.append(Spacer(1,12))

    if ruta_comb:
        elementos.append(Paragraph("Gráfico de Tendencias", styles['Heading2']))
        elementos.append(RLImage(ruta_comb, width=500, height=200))
        elementos.append(Spacer(1,12))

    pp = [s-d for s,d in zip(sistolica, diastolica)]
    dp = [s*p for s,p in zip(sistolica, ppm)]
    indices_diurno = [i for i,h in enumerate(hora) if 7 <= h < 22]
    indices_nocturno = [i for i,h in enumerate(hora) if h < 7 or h >= 22]

    resumen_total = {
        "Sistolica": calcular_resumen(sistolica),
        "Diastolica": calcular_resumen(diastolica),
        "PAM": calcular_resumen(pam),
        "PPM": calcular_resumen(ppm),
        "PP": calcular_resumen(pp),
        "DP": calcular_resumen(dp)
    }
    resumen_diurno = {k: calcular_resumen([v[i] for i in indices_diurno if i < len(v)]) for k,v in zip(resumen_total.keys(), [sistolica, diastolica, pam, ppm, pp, dp])}
    resumen_nocturno = {k: calcular_resumen([v[i] for i in indices_nocturno if i < len(v)]) for k,v in zip(resumen_total.keys(), [sistolica, diastolica, pam, ppm, pp, dp])}

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

    # tabla principal PDF
    tabla_datos = [["N°","Sistólica","Diastólica","PAM","PPM","PP (S-D)","DP (S×PPM)","Hora","Fecha"]]
    n = max(len(sistolica), len(diastolica), len(pam), len(ppm))
    for i in range(n):
        hora_str = f"{hora[i]:02d}:{minutos[i]:02d}" if (i < len(hora) and i < len(minutos)) else ""
        fecha_str = f"{dia[i]:02d}/{mes[i]:02d}/{ano[i]}" if (i < len(dia) and i < len(mes) and i < len(ano)) else ""
        tabla_datos.append([
            str(i+1),
            str(sistolica[i]) if i < len(sistolica) else "",
            str(diastolica[i]) if i < len(diastolica) else "",
            str(pam[i]) if i < len(pam) else "",
            str(ppm[i]) if i < len(ppm) else "",
            str(pp[i]) if i < len(pp) else "",
            str(dp[i]) if i < len(dp) else "",
            hora_str,
            fecha_str
        ])

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
