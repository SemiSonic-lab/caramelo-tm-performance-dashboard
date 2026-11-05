# Caramelo TM — Team Performance Dashboard

Dashboard público de estadísticas del equipo, construido con Streamlit.

## Archivos
- `app.py`: aplicación principal.
- `Caramelo TM.xlsx`: fuente de datos.
- `requirements.txt`: dependencias.

## Importante sobre el Excel
La aplicación lee exclusivamente la hoja **Caramelo**. La hoja **Capitanias** se ignora intencionalmente.
Los registros sin nombre en la columna `Integrante` se excluyen automáticamente.

## Ejecutar localmente
1. Instala Python 3.10 o superior.
2. Abre una terminal en esta carpeta.
3. Ejecuta:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar gratis en Streamlit Community Cloud
1. Sube estos tres archivos a un repositorio GitHub.
2. Entra a https://share.streamlit.io/
3. Selecciona `Deploy an app`.
4. Selecciona el repositorio, la rama principal y `app.py`.
5. Pulsa `Deploy`.

## Actualizar los datos
Reemplaza `Caramelo TM.xlsx` por la versión actualizada en GitHub, conservando:
- el nombre exacto del archivo;
- la hoja `Caramelo`;
- los nombres de las columnas que usa el dashboard.

Streamlit Cloud detectará el cambio del repositorio y volverá a desplegar la aplicación.

## Consideraciones
- El acceso a la aplicación es público si el repositorio y la app se configuran como públicos.
- No subas información confidencial o personal que no deba ser visible para todos.
- El archivo Excel queda publicado en el repositorio junto con la aplicación. Si no deseas que el público descargue el Excel original, se debe diseñar una arquitectura alternativa con almacenamiento privado.
