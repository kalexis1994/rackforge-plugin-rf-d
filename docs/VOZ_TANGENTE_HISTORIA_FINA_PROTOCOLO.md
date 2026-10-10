# Respuestas con perturbación de corriente menor

2026-10-10. Complementa el [banco original](VOZ_TANGENTE_HISTORIA_PROTOCOLO.md).
El intento nativo 03 rechaza STEP_PLUS,9,117,NoDecrease y su replay repite
ese rechazo. Conservar fuente y binarios parciales, sin interpretar el
rechazo como fallo de derivada ni como diagnóstico físico del macromodelo.

Solo los solves perturbados de respuesta usan 0,1/0,05 nA para direcciones
de corriente; las direcciones de tensión conservan 10/5 µV. Hx a etapas
absolutas fijas conserva 10/5 nA y 10/5 µV en sus 200 columnas.
Todos los gates, escenas, 48 pasos y biblioteca siguen iguales.
El codec RFJHIST2 declara ε de respuesta por dirección, además de su índice.
No deducir el tamaño de perturbación del tipo de coordenada al decodificar.
