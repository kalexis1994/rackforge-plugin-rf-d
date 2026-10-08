# Metadatos del adaptador de descomposición

Intentos01/02 pasan los mismos nueve pares de raíces cargadas, repetición y rechazo atómico; luego fallan con `KeyError('dt_s')` al consultar un campo que el recibo SDIRK no contiene. Ambos se conservan íntegros con fuentes/hash y casos canónicos idénticos. No pasan publicación completa.

El intento03 liga explícitamente cada recibo a su mínimo previamente congelado: half8/4 ticks de 125 ns/65536, y usa `GAMMA` y `WEIGHT` de la referencia SDIRK. La revisión del adaptador también encuentra el nombre incorrecto `A` antes de ejecutar de nuevo esa rama; la referencia expone `WEIGHT`. Se eliminan ambas suposiciones de interfaz. Ningún dato físico, solve, semilla, estado, gate o ecuación de etapa cambia. Se repite el banco completo antes de admitir la descomposición.
