# Reconstrucción del corpus de trayectorias compensadas

La auditoría ampliada conserva los informes y recibos de ventanas anteriores
y añade el [reloj completo](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md)
y el [controlador propio](BIESTABLE_CONTROLADOR_COMPENSADO_RESULTADOS.md).
Ocho informes/recibos fijan **149 entradas vigentes**, reconstruidas desde
blobs de `719817a`: **146 idénticas** y tres excepciones LF/CRLF históricas.

Las tres fuentes históricas completas conservan sus bytes, SHA del blob,
SHA del archivo usado y única transformación declarada. También se
conserva una versión anterior de prueba nunca commiteada, reconstruida
exclusivamente desde su recibo fallido identificado. La versión vigente
se recupera de Git; cualquier versión previa sin fuente/SHA/ruta/comando
e índice de intento se rechaza. No se normaliza ni modifica evidencia.

[Paquete](../evidence/loudness_latch_bdf_static_precision_path_inputs.json.gz):
**321.369 bytes**, SHA256 comprimido
`6debd03a2411368f18e49dc58e8be3b6508f538898d94cd9377c46f3ff28e1b2`;
SHA256 JSON canónico
`9555b78aa65555cebdef5eef1013cc4f7a521553cebbf928960cc357bdbc4563`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_path_inputs_summary.json)
conserva identidades, pertenencia a informes y versiones archivadas.

El [recibo](../evidence/loudness_latch_bdf_static_precision_path_inputs_validation.json)
registra **2/2 pruebas**, un intento exitoso, 18,3595 s, entradas intactas:
149 reconstrucciones desde blobs/excepciones, fuente anterior por recibo,
almacenamiento canónico y rechazo de alteraciones. Junto con cuatro pruebas
del reloj y cinco del controlador, el corte suma **11 pruebas nuevas**.
No se repite la suite histórica completa.

`python tools/validate_bdf_static_precision_path_inputs.py`

Para reproducir, materializar cada entrada por su SHA en un checkout aislado,
incluyendo las tres fuentes exactas archivadas; no asumir finales de línea
predeterminados del sistema. Los JSON nuevos usan la política `-text` local
preexistente. No cambia `.gitattributes` raíz ni políticas históricas.
Reconstrucción de bytes y equivalencia del controlador no demuestran
portabilidad numérica, error temporal global, hardware, audio o deadline.
