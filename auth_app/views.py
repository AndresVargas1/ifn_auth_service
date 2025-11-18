from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from .mongo import users_collection, logs_collection
from .schemas import validar_usuario, crear_log

class RegistrarUsuarioView(APIView):
    def post(self, request):
        try:
            data = validar_usuario(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        data['clave'] = make_password(data['clave'])
        # Insertar usuario
        result = users_collection.insert_one(data)

        return Response(
            {"id": str(result.inserted_id)},
            status=status.HTTP_201_CREATED
        )

class LoginUsuarioView(APIView):
    def post(self, request):
        identificacion = request.data.get("identificacion")
        clave = request.data.get("clave")

        if not identificacion or not clave:
            return Response(
                {"error": "identificación y clave son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = users_collection.find_one({"identificacion": identificacion})

        if not user:
            return Response(
                {"error": "usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if not check_password(clave, user["clave"]):
            return Response(
                {"error": "clave incorrecta"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # if user["fecha_fin_jwt"] and (user["fecha_fin_jwt"] > user["fecha_creacion_jwt"]):
        #     return Response(
        #         {"error": "El usuario ya tiene una sesión activa"},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        ahora = datetime.utcnow()
        fin = ahora + timedelta(hours=2)

        payload = {
            "identificacion": user["identificacion"],
            "iat": ahora,
            "exp": fin,
        }

        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        # Dependiendo de la versión de PyJWT, token puede ser bytes
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        # Guardar JWT y fechas en Mongo
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "jwt": token,
                    "fecha_creacion_jwt": ahora,
                    "fecha_fin_jwt": fin
                }
            }
        )

        # Registrar log de login
        logs_collection.insert_one(
            crear_log(identificacion, "Inicio de sesión")
        )

        return Response(
            {
                "jwt": token,
                "expira": fin.isoformat()
            },
            status=status.HTTP_200_OK
        )
class SessionStatusView(APIView):

    def post(self, request):
        token = request.data.get("jwt")
        identificacion = request.data.get("identificacion")

        if not token and not identificacion:
            return Response(
                {"error": "Debes enviar jwt o identificacion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = None
        motivo = None

        if token:
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"]
                )
                identificacion_from_token = payload.get("identificacion")

                if identificacion and identificacion != identificacion_from_token:
                    return Response(
                        {
                            "activa": False,
                            "motivo": "La identificación no coincide con el token"
                        },
                        status=status.HTTP_200_OK
                    )

                identificacion = identificacion_from_token

            except jwt.ExpiredSignatureError:
                motivo = "El token está vencido"
            except jwt.InvalidTokenError:
                motivo = "Token inválido"

            if motivo:
                return Response(
                    {
                        "activa": False,
                        "motivo": motivo
                    },
                    status=status.HTTP_200_OK
                )

        if identificacion:
            user = users_collection.find_one({"identificacion": identificacion})

        if not user:
            return Response(
                {
                    "activa": False,
                    "motivo": "Usuario o sesión no encontrada"
                },
                status=status.HTTP_200_OK
            )

        jwt_guardado = user.get("jwt")
        fecha_fin_jwt = user.get("fecha_fin_jwt")

        if not jwt_guardado or not fecha_fin_jwt:
            return Response(
                {
                    "activa": False,
                    "motivo": "El usuario no tiene una sesión activa"
                },
                status=status.HTTP_200_OK
            )

        ahora = datetime.utcnow()

        if ahora > fecha_fin_jwt:
            return Response(
                {
                    "activa": False,
                    "motivo": "El token almacenado está vencido"
                },
                status=status.HTTP_200_OK
            )

        if token and token != jwt_guardado:
            return Response(
                {
                    "activa": False,
                    "motivo": "El token no coincide con el registrado para el usuario"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "activa": True,
                "motivo": "Sesión válida",
                "identificacion": user.get("identificacion"),
            },
            status=status.HTTP_200_OK
        )

class LogoutUsuarioView(APIView):
    def post(self, request):
        identificacion = request.data.get("identificacion")

        if  not identificacion:
            return Response(
                {"error": "Debes enviar identificacion"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = users_collection.find_one({"identificacion": identificacion})

        if not user:
            return Response(
                {
                    "ok": False,
                    "mensaje": "Usuario no encontrado"
                },
                status=status.HTTP_200_OK
            )

        # Limpiar datos de sesión
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "jwt": None,
                    "fecha_creacion_jwt": None,
                    "fecha_fin_jwt": None
                }
            }
        )

        # Registrar log de logout
        logs_collection.insert_one(
            crear_log(identificacion, "Cierre de sesión")
        )

        return Response(
            {
                "ok": True,
                "mensaje": "Sesión cerrada correctamente"
            },
            status=status.HTTP_200_OK
        )
