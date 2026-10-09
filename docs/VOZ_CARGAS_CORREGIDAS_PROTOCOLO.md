# Cierre y liberación de la corrección conjunta

2026-10-09. Continuación de la
[respuesta estática](VOZ_CARGAS_RESPUESTA_FINA_PROTOCOLO.md).
La [predicción](../evidence/voice_joint_charge_response_fine_reference01.json)
propone objetivos para las 18 cargas; no acredita su deriva periódica.

Usar los dos vectores high/low del predictor, exportados sin redondear
de nuevo a un único float. El export verifica la descomposición normalizada
y la diferencia con los objetivos anteriores. No cambiar componentes,
fuentes, controles, fase o biblioteca física. No mezclar la memoria de una
historia con la trayectoria de otra.

Reutilizar exactamente el condicionador y caller de
[raíces y liberaciones anteriores](VOZ_CARGAS_SEMILLA_PROTOCOLO.md):
solo cambiar el archivo de objetivos del caller. Dos memorias y dos
semillas iniciales por memoria; cuatro raíces de 218 ecuaciones.
Newton y gates nativos/independientes iguales al banco de respuesta.
Las dos semillas deben coincidir dentro de 1e-6 V/1e-9 A,
incluidas corrientes de retención. NaN en objetivo/estado debe rechazarse.

Desde cada raíz guess=0, liberar a reloj cero hasta 2 µs/1.048.576 ticks,
máxima media etapa 125 y 62,5 ns. Como en el banco anterior: LTE
2e-6 V/2e-9 A, presupuesto 512 intervalos, 20 intentos; BUS/C1 KCL≤1e-12 A.
Comparar las 200 coordenadas a igual reloj entre resoluciones; cuatro
restore replays exactos. Contrastar etapas del primer y último intervalo:
24 pares de 400 ecuaciones, 48 puntos de etapa y ocho LTE independientes.

Recursos iguales: caller contra biblioteca congelada, stack 32 MiB,
180 s por proceso/600 s global, reserva 1 GiB más 8 MiB de outputs.
Preservar fallos y replays. Solo admitir cierre no lineal y liberación corta
de estos objetivos. Su mejora de deriva exige ciclos propios y consecutivos
a dos resoluciones; no se admite periodicidad, fidelidad física, nuevo
audio, encendido físico, SPICE o RT por esta prueba.
