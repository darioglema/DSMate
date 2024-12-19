import pandas as pd
import yaml
import re

def process_students_data(excel_file: str, output_yaml: str):
    # Leer los datos desde el archivo Excel
    df = pd.read_excel(excel_file, skiprows=9) # Cargar Excel del SIES eliminando columnas innecesarias

    # Crear una estructura para el archivo YAML
    data = {
        'cookie': {
            'expiry_days': 30,
            'key': 'some_signature_key',  # Aquí puedes poner la clave que necesites
            'name': 'some_cookie_name'
        },
        'credentials': {
            'usernames': {}
        }
    }

    # Procesar cada fila para llenar las credenciales
    for _, row in df.iterrows():
        # Extraer el DNI como contraseña
        password = row['DNI']
        
        # Extraer el email y el usuario
        email = row['Email']
        username = email.split('@')[0]
        
        # Extraer nombre y apellidos del campo "Alumno"
        full_name = row['Alumno']
        first_name, last_name = full_name.split(', ')[::-1]  # Asumimos el formato "apellido1 apellido2, nombre"

        # Añadir la información del usuario al diccionario
        data['credentials']['usernames'][username] = {
            'email': email,
            'failed_login_attempts': 0,
            'first_name': first_name,
            'last_name': last_name,
            'logged_in': False,
            'password': password 
        }

    # Escribir los datos en un archivo YAML
    with open(output_yaml, 'w') as file:
        yaml.dump(data, file, default_flow_style=False, allow_unicode=True)

# Llamada a la función con el archivo de entrada y el archivo de salida
process_students_data('alumnosMatriculados.xls', 'credentials.yaml')
