import streamlit as st
import sys
import os

from CRM.odoo_api_calls import create_lead_full_data

from airregio_agents_crm_simple import (
    extraer_datos_conversacion,
    calificar_conversacion,
)

st.title("Extractor de Información de Chat para CRM")

# Inicializar session_state si no existe
if "datos" not in st.session_state:
    st.session_state["datos"] = {}
if "datos_editados" not in st.session_state:
    st.session_state["datos_editados"] = {}
if "mostrar_formulario" not in st.session_state:
    st.session_state["mostrar_formulario"] = False

# Área de texto para pegar la conversación
conversation = st.text_area(
    "Pegua aquí una conversación de WhatsApp o cadena de correo y el agente IA extraerá la información para subirla al CRM de tu empresa."
)

# Botón para extraer información
if st.button("Extraer Información"):
    if conversation.strip() != "":
        # Llamar a las funciones para extraer datos y calificación
        datos_conversacion = extraer_datos_conversacion(conversation)
        calificacion = calificar_conversacion(conversation)

        # Combinar los datos obtenidos
        st.session_state["datos"] = {**datos_conversacion, **calificacion}
        st.session_state["mostrar_formulario"] = True
    else:
        st.warning("Por favor, pegue la conversación de WhatsApp antes de continuar.")

# Mostrar el formulario si los datos han sido extraídos
if st.session_state.get("mostrar_formulario", False):
    st.write("Edite los datos extraídos si es necesario:")

    datos = st.session_state["datos"]

    # Mostrar campos editables para los datos extraídos
    contact_name = st.text_input("Nombre del Contacto", datos.get("contact_name", ""))
    partner_name = st.text_input("Nombre de la Compañía", datos.get("partner_name", ""))
    phone = st.text_input("Teléfono", datos.get("phone", ""))
    email_from = st.text_input("Correo Electrónico", datos.get("email_from", ""))
    description = st.text_area("Descripción", datos.get("description", ""))
    conversation_name = st.text_input(
        "Nombre de la Conversación", datos.get("conversation_name", "")
    )
    tag_ids = st.text_input(
        "IDs de Etiquetas (separados por comas)",
        ", ".join(map(str, datos.get("tag_ids", []))),
    )
    street = st.text_input("Calle", datos.get("street", ""))
    score_total = datos.get("score_total", 0)
    st.write(f"Puntuación Total: {score_total}")

    # Determinar prioridad basada en score_total
    if score_total < 33:
        priority = "1"
    elif 34 <= score_total <= 66:
        priority = "2"
    else:
        priority = "3"

    st.write(f"Prioridad: {priority}")

    # Actualizar datos editados en session_state
    st.session_state["datos_editados"] = {
        "contact_name": contact_name,
        "partner_name": partner_name,
        "phone": phone,
        "email_from": email_from,
        "description": description,
        "conversation_name": conversation_name,
        "tag_ids": tag_ids,
        "street": street,
        "score_total": score_total,
        "priority": priority,
    }

    # Botón para enviar datos al CRM
    if st.button("Enviar a CRM"):
        datos_editados = st.session_state["datos_editados"]

        # Preparar datos para la función create_lead_full_data
        lead_name = datos_editados["conversation_name"]
        phone_number_id = datos_editados["phone"]
        contact_name = (
            datos_editados["contact_name"]
            if datos_editados["contact_name"] != ""
            else None
        )
        email_from = (
            datos_editados["email_from"] if datos_editados["email_from"] != "" else None
        )
        partner_name = (
            datos_editados["partner_name"]
            if datos_editados["partner_name"] != ""
            else None
        )
        description = (
            datos_editados["description"]
            if datos_editados["description"] != ""
            else None
        )
        tag_ids_list = (
            [int(tag.strip()) for tag in datos_editados["tag_ids"].split(",")]
            if datos_editados["tag_ids"] != ""
            else None
        )
        street = datos_editados["street"] if datos_editados["street"] != "" else None
        priority = datos_editados["priority"]

        # Llamar a la función para crear el lead en el CRM
        create_lead_full_data(
            lead_name=lead_name,
            phone_number_id=phone_number_id,
            contact_name=contact_name,
            email_from=email_from,
            partner_name=partner_name,
            description=description,
            priority=priority,
            tag_ids=tag_ids_list,
            street=street,
            stage_id=None,
        )
        st.success("Los datos han sido actualizados")

        # Reiniciar el estado para permitir nuevas entradas
        st.session_state["mostrar_formulario"] = False
        st.session_state["datos"] = {}
        st.session_state["datos_editados"] = {}
