from flask import Flask, request, render_template_string
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def generar_grafico(titulo, valores):
    fig, ax = plt.subplots(figsize=(10, 3))  # Más largo en eje X
    ax.plot(valores, marker='o')
    ax.set_title(titulo)
    ax.set_ylabel("Presión (mmHg)")
    ax.set_xlabel("Tiempo")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Obtener datos del formulario
        nombre = request.form.get("nombre", "N/A")
        apellido = request.form.get("apellido", "N/A")
        dni = request.form.get("dni", "N/A")
        edad = request.form.get("edad", "N/A")
        tiempo = request.form.get("tiempo", "N/A")

        # Simular mediciones
        sistolica = [random.randint(110, 140) for _ in range(72)]
        diastolica = [random.randint(70, 90) for _ in range(72)]

        img_sis = generar_grafico("Presión Sistólica", sistolica)
        img_dia = generar_grafico("Presión Diastólica", diastolica)

        # Crear filas para la tabla
        filas = "".join(
            f"<tr><td>{i+1}</td><td>{s}</td><td>{d}</td></tr>"
            for i, (s, d) in enumerate(zip(sistolica, diastolica))
        )

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
                <h2>Presión Sistólica</h2>
                <img src="data:image/png;base64,{img_sis}">

                <h2>Presión Diastólica</h2>
                <img src="data:image/png;base64,{img_dia}">
            </div>

            <table>
                <tr><th>N°</th><th>Sistólica</th><th>Diastólica</th></tr>
                {filas}
            </table>

            <br><a href="/">Volver</a>
        </body>
        </html>
        """
        return html

    # Si es GET, mostrar el formulario
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

if __name__ == "__main__":
    app.run(debug=True)


