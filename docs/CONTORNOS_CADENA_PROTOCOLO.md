# Ambos contornos con ladder, VCA y salida

Protocolo previo a medición, 2026-10-14. Revisión nominal CA3046 y dispositivos
condicionados de C5/gatillo; fuentes SVC-9 Fig.9-7 p.9, Fig.9-11 p.13,
Fig.9-8 p.10 y Fig.9-17 p.19. No hay unidad física de referencia.

## Unión eléctrica

Promover VCA_BASE y TAIL a incógnitas. Compartir Q26/Q28 entre placa 2 y
cadena: retirar las cuatro filas de control heredadas, su R60 en TAIL y
C18 heredado; conservar Q26/Q28/R60/C18 del contorno exactamente una vez.
Retirar la fuente de loudness de la cadena y conservar R59 entre el contorno
y la base real del primer VCA. C2/C5/C7 y las seis junturas de gatillo/latch
conservan sus cargas durante todos los trials. Red nativa: 118 nodos; Amount
eliminado por estrella exacta. Referencia: estrella original con cursor propio.

Panel fijo heredado: Attack volumen 1 kohm, Decay 10 kohm; Attack filtro
0 ohm más R1 100 ohm, Decay 1 kohm; ambos Sustain 0.5, Amount 0.5,
Cutoff 0.5, Range 0.1, Scale 250 ohm, R61 200 ohm y R14 25 kohm.
Dispositivos nominales, mismas hipótesis y conflictos documentales del bloque
C5. El segundo VCA recibe 2 V impuestos; no afirmar dominio general del panel.

## Banco y aceptación

DC propio de la red conjunta, inicializado desde soluciones aisladas sólo
como semilla numérica; no prolonga la historia audible anterior. Estímulo
eléctrico de laboratorio: OSC1 del mixer ON, fuente sinusoidal 100 Hz,
0.2 V pico desde 1 ms; demás ramas OFF. Esta fuente no modela un oscilador.
KEY 0/10 V con cambios a 1,10,20,30 ms; final 36 ms. Opcionales C11/C12 OFF.
Comparar propuestas máximas 8 y 4 us, observaciones comunes cada 250 us.
Radau de dos etapas con step doubling; gates locales 0.2 uV + 2e-7 |V|,
Newton 1 pA y 2 nV. Sin conmutación de latch ni reinicio de capacitores.

Antes de promover: reloj completo de ambas escenas, finitud, corriente
R59 y R60 no impuestas, DC original con FD completo; columnas DC y masa
de candidatos seleccionados y residual Radau original con historia fija.
Gates FD 2 nS + 2e-5 |J|; KCL original 20 pA y corrección 2 nV;
refinamiento todos los nodos 20 uV + 2e-6 |V| y cargas 2 nA + 2e-5 |I|.
Rechazos inválidos deben preservar el estado. Conservar fallos y replay
sin cambios antes de reparar. No requerir igualdad con el contorno aislado:
ahora existen cargas eléctricas distintas.

Límites: 1 GiB libre mínimo, 32 MiB de archivos nuevos, compilación 120 s,
cada perfil nativo 300 s, auditor 300 s. No Cargo ni biblioteca nueva.
No cambiar evidencia histórica. Audio, si se exporta, debe declarar duración
real simulada, escala fija y resampling; no repetir ciclos para fingir notas.
Este banco no admite fidelidad física, voz con VCO ni tiempo real.
