from datetime import datetime

def validar_usuario(data):
    required = ["nombre", "apellido", "identificacion", "clave"]
    for field in required:
        if field not in data or not data[field]:
            raise ValueError(f"El campo {field} es obligatorio")
    
    return {
        "nombre": data["nombre"],
        "apellido": data["apellido"],
        "identificacion": data["identificacion"],
        "clave": data["clave"], 
        "jwt": None,
        "fecha_creacion_jwt": None,
        "fecha_fin_jwt": None,
    }


def crear_log(identificacion_usuario, descripcion):
    return {
        "identificacion_usuario": identificacion_usuario,
        "descripcion": descripcion,
        "fecha": datetime.utcnow()
    }
