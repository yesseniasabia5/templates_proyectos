"""
#================================================== 
Script: modal_slack.py
Descripción: - Define la estructura del modal de Slack para el ingreso de datos numéricos y fechas.
Description: - Defines the structure of the Slack modal for entering numeric data and date ranges.
Author: Yessenia Sabia
#==================================================
"""
def modal_view(fecha_inicio, fecha_fin):
    return {
                "type": "modal",
                "callback_id": "modal_cargar_datos",
                "title": {"type": "plain_text", "text": "BOT ABC"},
                "submit": {"type": "plain_text", "text": "Enviar"},
                "close": {"type": "plain_text", "text": "Cancelar"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "fecha_inicio",
                        "label": {"type": "plain_text", "text": "Fecha de Inicio"},
                        "element": {
                            "type": "datepicker",
                            "initial_date": f"{fecha_inicio}",
                            "action_id": "datepicker-action"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "fecha_fin",
                        "label": {"type": "plain_text", "text": "Fecha de Fin"},
                        "element": {
                            "type": "datepicker",
                            "initial_date": f"{fecha_fin}",
                            "action_id": "datepicker-action"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_1",
                        "label": {"type": "plain_text", "text": "Field 1"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "11110424922.77",
                            "is_decimal_allowed": True,
                            "action_id": "field_1-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_2",
                        "label": {"type": "plain_text", "text": "Field 2"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "458148.64",
                            "is_decimal_allowed": True,
                            "action_id": "field_2-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_3",
                        "label": {"type": "plain_text", "text": "Field 3"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "6975.74",
                            "is_decimal_allowed": True,
                            "action_id": "field_3-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_4",
                        "label": {"type": "plain_text", "text": "Field 4"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "-576854.47",
                            "is_decimal_allowed": True,
                            "action_id": "field_4-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_5",
                        "label": {"type": "plain_text", "text": "Field 5"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "1464.91",
                            "is_decimal_allowed": True,
                            "action_id": "field_5-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_6",
                        "label": {"type": "plain_text", "text": "Field 6"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "1965983.25",
                            "is_decimal_allowed": True,
                            "action_id": "field_6-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "field_7",
                        "label": {"type": "plain_text", "text": "Field 7"},
                        "element": {
                            "type": "number_input",
                            #"initial_value": "412856.48",
                            "is_decimal_allowed": True,
                            "action_id": "field_7-action",
                            "placeholder": {"type": "plain_text", "text": "Ingrese un importe"}
                        }
                    }
                ]
            }
