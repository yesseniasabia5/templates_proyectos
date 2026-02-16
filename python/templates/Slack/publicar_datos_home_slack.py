"""
#==================================================
Script: publicar_datos_home_slack.py
Descripción: - Publica los resultados del procesamiento de datos en la Home Tab de Slack.
Description: - Publishes the results of data processing on the Slack Home Tab.
Author: Yessenia Sabia
#==================================================
"""
from slack_bot import slack_client
from decimal import Decimal
import logging as log

# Función para publicar el resultado en la Home Tab de Slack
def publicar_resultado_home_slack(shared_data, resultado_final):
    user_id = shared_data.get("user_id")
    if user_id:
        # Armamos un mensaje de resumen con la 'diferencia' u otros datos
        header = ["Campo1", "Campo2", "Campo3", "Campo4", "Campo5", "Campo6"]
        column_widths = [60, 3, 23, 23, 17, 9]

        # Función auxiliar para formatear una fila de datos
        def format_row(row, widths):
            return " | ".join(str(item).ljust(width) if isinstance(item, str) else f"{item:,.6f}".rjust(width) for item, width in zip(row, widths))

        formatted_header = format_row(header, column_widths)
        separator = "-|-".join("-" * width for width in column_widths)
        formatted_data = [format_row(
            [x['campo1'], x['campo2'], x['campo3'], x['campo4'], round(Decimal(x['campo5']), 6), '' if x['campo6'] == '' else round(Decimal(x['campo7']), 6)], column_widths
        ) for x in resultado_final]

        table = f"{formatted_header}\n{separator}\n" + "\n".join(formatted_data)
        table_markdown = f"```\n{table}\n```"
        resultado_str = f""" 
        :small_blue_diamond:Fecha de inicio: {shared_data['fecha_inicio']} | Fecha de Fin: {shared_data['fecha_fin']}\n
        {table_markdown}
        """

        slack_client.publicar_home_tab(user_id, result=resultado_str)
        log.info(f"Se publicó la Home Tab para el user_id={user_id}")