"""
#==================================================
Script: slack_bot.py
Descripción: - Maneja la interacción con Slack, incluyendo el envío de mensajes, apertura de modales y publicación de resultados.
             - Se conecta a Slack usando Socket Mode para recibir eventos e interacciones en tiempo real.
             - Permite enviar mensajes tanto vía Web API (HTTP) como vía WebSocket (Socket Mode).
             - Publica resultados en la Home Tab de Slack para el usuario que interactuó con el modal.

Description: - Handles interaction with Slack, including sending messages, opening modals, and publishing results.
             - Connects to Slack using Socket Mode to receive real-time events and interactions.
             - Allows sending messages both via Web API (HTTP) and via WebSocket (Socket Mode).
             - Publishes results on the Slack Home Tab for the user who interacted with the modal.  
Author: Yessenia Sabia
#==================================================
"""
import logging as log
import os
from pydoc import text
import requests
from Slack.modal_slack import modal_view_form
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from datetime import datetime

# Cargar los secretos al inicio

SLACK_BOT_TOKEN = "XXXXX" #aca va el token de autenticación del bot de Slack, se puede cargar desde una variable de entorno o secreto
CHANNEL_IDS = "XXXXX","YYYYY" #aca va el ID del canal de Slack donde se enviarán los mensajes, se puede cargar desde una variable de entorno o secreto. Si son varios canales, se pueden agregar a la lista.
SLACK_APP_TOKEN = "XXXXX" #aca va el token de autenticación de la aplicación de Slack para Socket Mode (token xapp-...), se puede cargar desde una variable de entorno o secreto

log.basicConfig(level=log.DEBUG)

class SlackClient:
    def __init__(self, token, channel_ids):
        self.client = WebClient(token=token)
        self.channel_ids = channel_ids if isinstance(channel_ids, list) else [channel_ids]
        self.socket_mode_client = None 

    # Función para establecer datos compartidos
    def set_shared_data(self, shared_data):
        """
        Recibe el diccionario compartido desde main.py 
        y lo guarda internamente para poder asignar valores al recibir el modal.
        """
        self.shared_data = shared_data    

    # Función para iniciar el cliente de Socket Mode y conectarse con Slack vía WebSocket
    def start_socket_mode(self):
        """
        Inicializa el cliente de Socket Mode y se conecta con Slack vía WebSocket.
        """
        try:
            self.socket_mode_client = SocketModeClient(
                app_token=SLACK_APP_TOKEN,  # Debe ser el token xapp-...
                web_client=self.client
            )
            # Registramos un listener genérico para procesar eventos e interacciones
            self.socket_mode_client.socket_mode_request_listeners.append(self.process)
            self.socket_mode_client.connect()
            log.info("Socket Mode iniciado y conectado correctamente.")
        except Exception as e:
            log.error(f"Error iniciando Socket Mode: {e}")

    # Función para procesar eventos e interacciones de Slack
    def process(self, client: SocketModeClient, req: SocketModeRequest):

        # Responde a Slack que recibimos el evento (obligatorio en Socket Mode)
        if req.envelope_id:
            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)

        # ~~~~~~~~~~~~~ MANEJO DE EVENTOS ~~~~~~~~~~~~~
        if req.type == "events_api":
            event = req.payload.get("event", {})
            event_type = event.get("type")

            # Ejemplo: si el mensaje no es de un bot (para evitar loops):
            if "bot_id" not in event and event_type == "message":
                channel = event.get("channel")
                user_text = event.get("text", "")
                log.info(f"Evento 'message' recibido: {user_text} en canal {channel}")
                # Aquí podrías responder algo automáticamente si lo deseas.

            # IMPORTANTE: Se omite la lógica "app_home_opened" 
            # para que NO se muestre nada automáticamente en la Home Tab.

        # ~~~~~~~~~~~~~ MANEJO DE INTERACCIONES ~~~~~~~~~~~~~
        if req.type == "interactive":
            payload = req.payload

            # Caso de un botón presionado => "block_actions"
            if payload.get("type") == "block_actions":
                # Obtiene el trigger_id para abrir el modal
                trigger_id = payload["trigger_id"]

                # Armamos la vista (modal) tal como la tenías antes
                # Función para calcular las fechas del formulario
                try:
                    client.web_client.views_open(trigger_id=trigger_id, view=modal_view_form)
                except SlackApiError as e:
                    log.error(f"Error al abrir el modal vía Socket Mode: {e.response['error']}")

            # Caso “view_submission” => cuando se envía el modal
            elif payload.get("type") == "view_submission":
                state = payload["view"]["state"]["values"]
                user_id = payload["user"]["id"]
                fecha_inicio = state["fecha_inicio"]["datepicker-action"]["selected_date"]
                fecha_fin = state["fecha_fin"]["datepicker-action"]["selected_date"]
                field_1 = state["field_1"]["field_1-action"]["value"]
                field_2 = state["field_2"]["field_2-action"]["value"]
                field_3 = state["field_3"]["field_3-action"]["value"]
                field_4 = state["field_4"]["field_4-action"]["value"]
                field_5 = state["field_5"]["field_5-action"]["value"]
                field_6 = state["field_6"]["field_6-action"]["value"]
                field_7 = state["field_7"]["field_7-action"]["value"]

                log.info("Datos recibidos del modal (Socket Mode):")
                log.info(f"Fecha Inicio: {fecha_inicio}")
                log.info(f"Fecha Fin: {fecha_fin}")
                log.info(f"Field1: {field_1}")
                log.info(f"Field2: {field_2}")
                log.info(f"Field3: {field_3}")
                log.info(f"Field4: {field_4}")
                log.info(f"Field5: {field_5}")
                log.info(f"Field6: {field_6}")
                log.info(f"Field7: {field_7}")

                # Guardar valores en shared_data (si existe)
                if self.shared_data is not None:
                    self.shared_data["fecha_inicio"] = fecha_inicio
                    self.shared_data["fecha_fin"] = fecha_fin
                    self.shared_data["field_1"] = field_1
                    self.shared_data["field_2"] = field_2
                    self.shared_data["field_3"] = field_3
                    self.shared_data["field_4"] = field_4
                    self.shared_data["field_5"] = field_5
                    self.shared_data["field_6"] = field_6
                    self.shared_data["field_7"] = field_7
                    self.shared_data["user_id"] = user_id

    # Función para enviar un mensaje a Slack con un botón interactivo
    def enviar_mensaje_con_boton(self):
            """
            Envía un mensaje a múltiples canales con un botón interactivo.
            """
            for channel_id in self.channel_ids:
                try:
                    response = self.client.chat_postMessage(
                        channel=channel_id,
                        text="🔔🤖¡Hola!",
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": text
                                },
                                "accessory": {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Ingresar",
                                        "emoji": True
                                    },
                                    "value": "cargar_datos",
                                    "action_id": "abrir_modal"
                                }
                            }
                        ]
                    )
                    log.info(f"Mensaje enviado a canal {channel_id}: {response['message']['text']}")
                except SlackApiError as e:
                    log.error(f"Error al enviar mensaje al canal {channel_id}: {e.response['error']}")

    # Función para enviar un mensaje a Slack usando un webhook (HTTP)
    def enviar_mensaje_via_webhook(self, endpoint, mensaje):
        """
        Envía un mensaje a Slack usando un webhook (HTTP).
        
        :param endpoint: URL del webhook
        :param mensaje: Texto del mensaje a enviar
        """
        try:
            payload = {
                "text": mensaje
            }
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            log.info(f"Mensaje enviado a Slack vía webhook: {mensaje}")
        except requests.exceptions.RequestException as e:
            log.error(f"Error al enviar mensaje vía webhook: {e}")

    # Función para enviar un mensaje a Slack usando Socket Mode (WebSocket)
    def enviar_mensaje_via_websocket(self, mensaje):
        """
        Envía un mensaje a Slack usando Socket Mode (WebSocket).
        Internamente sigue usando la Web API,
        pero la conexión con Slack está habilitada vía WebSocket.
        """
        if not self.socket_mode_client:
            log.warning("SocketModeClient no está inicializado. Llamar a start_socket_mode() primero.")
            return
        
        for channel_id in self.channel_ids:
            try:
                response = self.socket_mode_client.web_client.chat_postMessage(
                    channel=channel_id,
                    text=mensaje
                )
                log.info(f"Mensaje enviado a Slack vía WebSocket en canal {channel_id}: {mensaje}")
            except SlackApiError as e:
                log.error(f"Error al enviar mensaje vía WebSocket en canal {channel_id}: {e.response['error']}")

    # Función para publicar o actualizar la Home Tab de Slack para el usuario especificado
    def publicar_home_tab(self, user_id, result=None):
        """
        Publica o actualiza la Home Tab de Slack para el usuario especificado.
        Muestra algún 'result' que se haya calculado al enviar el modal.
        """
        if not self.socket_mode_client:
            log.warning("SocketModeClient no inicializado.")
            return

        resultado_texto = f"*A continuación los resultados de la ejecución de hoy {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:*\n{result}" if result else "No hay resultados (aún)."

        home_view = {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"¡Hola <@{user_id}>!"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": resultado_texto
                    }
                }
            ]
        }

        try:
            self.socket_mode_client.web_client.views_publish(
                user_id=user_id,
                view=home_view
            )
            log.info(f"Home Tab actualizada para el usuario {user_id}.")
        except SlackApiError as e:
            log.error(f"Error al publicar Home Tab: {e.response['error']}")

# Instancia global
slack_client = SlackClient(token=SLACK_BOT_TOKEN, channel_ids=CHANNEL_IDS)

if __name__ == "__main__":
    # 1) Iniciamos Socket Mode
    slack_client.start_socket_mode()
