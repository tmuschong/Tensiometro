from flask import Flask, render_template_string
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Función para generar una imagen de gráfico en base64
def generar_grafico(titulo, valores):
    fig, ax = plt.subplots()
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")

    # Convertimos el gráfico en imagen base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    imagen_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return imagen_base64

@app.route("/")
def home():
    # Simulamos 10 lecturas aleatorias
    sistolica = [random.randint(110, 140) for _ in range(72)]
    diastolica = [random.randint(70, 90) for _ in range(72)]

    img_sis = generar_grafico("Presión Sistólica", sistolica)
    img_dia = generar_grafico("Presión Diastólica", diastolica)

    # Plantilla HTML en línea
    html = """
    <html>
    <head>
        <title>Presiones Arteriales</title>
    </head>
    <body>
        <h1>Presión Sistólica</h1>
        <img src="data:image/png;base64,{{img_sis}}">
        <h1>Presión Diastólica</h1>
        <img src="data:image/png;base64,{{img_dia}}">
    </body>
    </html>
    """
    return render_template_string(html, img_sis=img_sis, img_dia=img_dia)

if __name__ == "__main__":
    app.run(debug=True)
