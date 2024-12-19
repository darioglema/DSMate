# Descripción
Asistente Virtual desarrollado por Darío González Lema para mejorar la asistencia a los estudiantes de Sistemas Distribuidos en el grado de Ingeniería Informática de la Escuela Politécnica de Gijón, Universidad de Oviedo.

# Instalación
Para probar este asistente se ha utilizando un servidor con Ubuntu Server 22.04.5 LTS con Python 3.10.12. Para instalar las dependencias necesarias para desplegar el sistema sigue estos pasos:

```
git clone https://github.com/darioglema/DSMate.git
pip install -r requirements.txt
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral:latest
```

Debes de añadir al directorio files/ todos los documentos que quieras que sean utilizados por es asistente.
En el archivo credentials.yaml se encuentras los usuarios que tienen acceso al sistema.
El script createCredentials.py crea un archivo credentials.yaml a partir de una lista de estudiantes descargada desde el SIES.

# Ejecución
Para ejecutar el asistente utiliza este comando

```
streamlit run app.py
```

Ahora puedes acceder al asistente localmente desde un navegador [http://localhost:8501/](http://localhost:8501/ "Asistente") o desde cualquier equipo con acceso a la tu red [http://<IP>:8501/](http://<IP>:8501/ "Asistente")