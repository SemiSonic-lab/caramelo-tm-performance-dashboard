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


## Histórico de rendimiento (Fase 5)

Después de reemplazar `Caramelo TM.xlsx` con una versión actualizada:

1. Abre la pestaña **Actions** del repositorio en GitHub.
2. Selecciona el flujo **Capturar histórico de rendimiento**.
3. Pulsa **Run workflow** y confirma la ejecución.
4. Cuando termine correctamente, el archivo `historico_indicadores.csv` quedará actualizado y el dashboard incorporará la nueva captura.

La captura lee exclusivamente la hoja `Caramelo` y conserva IGP total, carreras completadas, puntos de carrera, promedio de puntos por carrera, carreras ganadas y podios. Se registra como máximo una captura idéntica por día; si los datos permanecen iguales, se podrán conservar nuevas capturas en días posteriores para documentar esa estabilidad.

El flujo es manual y requiere permisos de escritura en el repositorio. No se almacenan credenciales dentro de la aplicación pública. Las capturas quedan en el repositorio, por lo que también son públicas si el repositorio es público. El histórico comienza en la primera ejecución y no reconstruye periodos anteriores.
