import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
import re


load_dotenv(override=True)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

llama_3_2 = "llama-3.2-90b-vision-preview"
llama_3_1 = "llama-3.1-70b-versatile"
gpt = "gpt-4o-mini"
# llm = ChatOpenAI(model=gpt, temperature=0.2)
llm = ChatGroq(model=llama_3_1, temperature=0.2)

############################## 1. Prepare data for CRM ##############################


# Define la estructura esperada de los datos utilizando Pydantic


class DatosUsuario(BaseModel):
    contact_name: Optional[str] = Field(
        default=None, description="Nombre del usuario o vacío si no se ha proporcionado"
    )
    email_from: Optional[str] = Field(
        default=None, description="Correo electrónico o vacío si no se ha proporcionado"
    )
    partner_name: Optional[str] = Field(
        default=None, description="Nombre de la Empresa o vacío si no aplica"
    )
    phone: Optional[str] = Field(
        default=None, description="Número de teléfono o vacío si no se ha proporcionado"
    )
    description: Optional[str] = Field(
        default=None,
        description="Resumen COMPLETO sobre la solicitud o vacío si no hay notas",
    )
    street: Optional[str] = Field(
        default=None, description="Dirección o vacío si no hay notas"
    )
    conversation_name: Optional[str] = Field(
        default=None,
        description="Nombre general de la conversación resumiendo la solicitud del usuario o vacío si no hay notas",
    )
    tag_ids: Optional[List[int]] = Field(
        default=None,
        description="Lista de IDs de las etiquetas asignadas a la conversación o vacío si no hay notas",
    )


# Función para extraer los datos del usuario a partir de la conversación
def extraer_datos_conversacion(mensajes):
    """
    Procesa una lista de mensajes entre el asistente y el usuario para extraer información clave.

    Args:
        mensajes (List[dict]): Lista de mensajes en el formato [{"role": "user", "content": "..."}, ...]

    Returns:
        Optional[dict]: Diccionario con los datos extraídos, solo con las claves encontradas.
    """

    # Crear una instancia del parser basado en la clase DatosUsuario
    parser = JsonOutputParser(pydantic_object=DatosUsuario)
    format_instructions = parser.get_format_instructions()

    # Crear las plantillas de prompt
    system_prompt_template = PromptTemplate.from_template(
        """
        Eres un asistente profesional de AIRREGIO especializado en extraer información clave de una conversación entre un asistente y un usuario.
        La información que extraigas será usada para ayudar a un vendedor a entender mejor la información de la conversación, llenar datos en su CRM y usarla para cerrar la venta.
        
        INSTRUCCIONES:
        - Únicamente extrae información contenida en los mensajes del usuario para llenar los valores del JSON. Los valores en los mensajes del asistente no deben ser usados para llenar el JSON.
        - Si no hay información útil, no extraigas nada.
        - Usa las respuestas del asistente solo como contexto o referencia para entender mejor la solicitud del usuario, pero **nunca** como fuente de valores para el JSON.
        - Los campos solo deben aparecer en el JSON si fueron mencionados explícitamente por el usuario.
        - La información que extraigas será usada para un vendedor por parte de Airregio
        - Presenta la información que extraigas de una manera que sea útil para el vendedor de Airregio para entender la conversación y pueda cerrar la venta.
        - Si hay algo urgente, menciona en al principio del parámetro conversation_name con la palabra 'URGENTE:'.
        - Usa el parámetro description para agregar toda la información que le sea útil al vendedor humano. Sobretodo si se agendó una fecha agrégalo aquí.
        
        
        Además, debes asignar una o más etiquetas numéricas en el parámetro tag_ids basadas en el tema de la conversación:
        1: URGENTE (si se menciona que es urgente)
        2: Mantenimiento (si se solicita mantenimiento)
        3: Consulta (Si solo es una consulta)
        4: Instalación (si se requiere instalación)
        5: Otro (si es otra categoría que no es ni urgente, ni mantenimiento, ni consulta, ni instalación)

        Solo incluye los campos en el JSON que correspondan a información explícita en los mensajes del usuario.
        
        Devuelve los datos en formato JSON, siguiendo las instrucciones:
        
        

        {format_instructions}
        """
    )

    user_prompt_template = PromptTemplate.from_template(
        """
        Procesa la siguiente conversación y extrae los datos del usuario:

        {mensajes}

        **Nota:** No debes incluir las interacciones del asistente en los campos de datos. si es necesario, solo usa esas interacciones del asistente para entender mejor la solicitud del usuario.
        """
    )

    # Rellenar el contenido del mensaje del sistema y del usuario
    system_message_content = system_prompt_template.format(
        format_instructions=format_instructions
    )

    user_message_content = user_prompt_template.format(mensajes=mensajes)

    try:
        # Invocar el LLM usando SystemMessage y HumanMessage
        json_datos_response = llm.invoke(
            [
                SystemMessage(content=system_message_content),
                HumanMessage(content=user_message_content),
            ]
        )

        # Validar y parsear la respuesta JSON
        datos_usuario = parser.parse(json_datos_response.content)

        # Convertir a diccionario eliminando las claves con valor None
        datos_dict = {k: v for k, v in datos_usuario.items() if v is not None}

        # print(f"TOOL extraer_datos_conversacion. Datos extraídos:\n\n{datos_dict}\n\nFin datos extraídos.")

        return datos_dict
    except Exception as e:
        print(f"Ocurrió un error al extraer los datos del usuario: {e}")
        return None


############################## 2. Score Chat  ##############################


# Define la estructura esperada de los datos utilizando Pydantic
class ScoreOutput(BaseModel):
    score_total: int = Field(
        description="Puntaje total asignado al lead según la conversación"
    )


# Función para limpiar la respuesta del LLM
def limpiar_respuesta(respuesta: str) -> str:
    """
    Limpia la respuesta del LLM eliminando cualquier etiqueta, texto adicional o bloques de código,
    dejando solo el JSON válido.
    """
    try:
        # Eliminar cualquier bloque de código con ```json ... ```
        json_block = re.search(r"```json\s*(\{.*?\})\s*```", respuesta, re.DOTALL)
        if json_block:
            return json_block.group(1).strip()

        # Si no hay bloques de código, intenta extraer el JSON directamente
        inicio = respuesta.find("{")
        fin = respuesta.rfind("}") + 1
        if inicio != -1 and fin != -1:
            json_str = respuesta[inicio:fin]
            return json_str.strip()

        # Si no se encuentra un JSON válido, retornar la respuesta completa para depuración
        return respuesta.strip()
    except Exception as e:
        print(f"Error al limpiar la respuesta: {e}")
        return respuesta.strip()


# Función para calificar la conversación y obtener el score_total en formato JSON
def calificar_conversacion(mensajes):
    """
    Procesa una lista de mensajes entre el agente y el usuario para calcular una calificación total.

    Args:
        mensajes (List[dict]): Lista de mensajes en el formato [{"role": "user", "content": "..."}, ...]

    Returns:
        Optional[dict]: Diccionario con el puntaje total, por ejemplo {"score_total": 75}.
    """

    # Crear una instancia del parser basado en la clase ScoreOutput
    parser = JsonOutputParser(pydantic_object=ScoreOutput)

    # Crear las plantillas de prompt
    # Escapar las llaves en el system_prompt_template
    system_prompt_template = PromptTemplate.from_template(
        """
        Eres un asistente experto en análisis de conversaciones para la calificación de leads. 
        Tu tarea es analizar la siguiente conversación entre un lead y un agente de AIRREGIO y asignar un puntaje total basado en los factores proporcionados.

        Califica al lead según la siguiente tabla de factores. Se te pasará una conversación entre un lead y un agente:

        1. **Urgencia de la Solicitud** (0 a 20 puntos):
           - No hay urgencia / Sin fecha específica: 0 puntos
           - Considera hacerlo en los próximos meses: 10 puntos
           - Necesita realizarlo dentro de 1-2 meses: 15 puntos
           - Urgencia alta (necesita empezar de inmediato): 20 puntos

        2. **Tamaño del Proyecto** (0 a 20 puntos):
           - Proyecto pequeño (terrazas, balcones): 5 puntos
           - Proyecto mediano (azoteas residenciales, techos verdes): 10 puntos
           - Proyecto grande (cubiertas industriales, plataformas, sótanos): 20 puntos

        3. **Sector del Cliente** (0 a 10 puntos):
           - Residencial: 5 puntos
           - Comercial: 7 puntos
           - Industrial: 10 puntos

        4. **Presupuesto Estimado** (0 a 15 puntos):
           - No menciona presupuesto: 0 puntos
           - Menciona un presupuesto bajo: 5 puntos
           - Menciona un presupuesto medio: 10 puntos
           - Menciona un presupuesto alto o flexible: 15 puntos

        5. **Interacciones Previas y Nivel de Interés** (0 a 20 puntos):
           - Interacción inicial / Información general: 5 puntos
           - Muestra interés específico en los servicios: 10 puntos
           - Ha tenido múltiples interacciones y pide detalles concretos: 15 puntos
           - Ha pedido cotizaciones y detalles técnicos precisos: 20 puntos

        6. **Análisis de Sentimiento y Actitud del Lead** (0 a 15 puntos):
           - Neutral o desinteresado: 5 puntos
           - Interesado y positivo: 10 puntos
           - Entusiasta o con alta motivación para avanzar: 15 puntos

        Suma los valores de cada factor y responde solo con el valor total del score en formato JSON. 
        No agregues ninguna explicación adicional, solamente el resultado en JSON.

        Ejemplo de respuesta correcta:
        ```json
        {{
            "score_total": 75
        }}
        ```
        """
    )

    user_prompt_template = PromptTemplate.from_template(
        """
        Procesa la siguiente conversación y calcula el score_total basado en los factores proporcionados:

        {mensajes}
        """
    )

    # Rellenar el contenido del mensaje del sistema y del usuario
    system_message_content = system_prompt_template.format()
    # Filtra solo HumanMessage y AIMessage, excluyendo ToolMessage

    user_message_content = user_prompt_template.format(mensajes=mensajes)

    try:
        # Invocar el LLM usando SystemMessage y HumanMessage
        json_score_response = llm.invoke(
            [
                SystemMessage(content=system_message_content),
                HumanMessage(content=user_message_content),
            ]
        )

        # Imprimir la respuesta completa del LLM para depuración
        # print("Respuesta del LLM:", json_score_response.content)

        # Limpia la respuesta para eliminar etiquetas adicionales
        respuesta_limpia = limpiar_respuesta(json_score_response.content)

        # Imprimir la respuesta limpia para depuración
        # print("Respuesta Limpia:", respuesta_limpia)

        # Validar y parsear la respuesta JSON
        score_output = parser.parse(respuesta_limpia)

        # Dado que score_output ya es un dict, puedes usarlo directamente
        score_dict = score_output  # score_output es un dict

        return score_dict
    except Exception as e:
        print(f"Ocurrió un error al calificar la conversación: {e}")
        return None
