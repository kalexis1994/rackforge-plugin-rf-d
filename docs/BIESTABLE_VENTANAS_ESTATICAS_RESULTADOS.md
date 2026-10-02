# Precisión de los sellos durante 64 intervalos guardados

El [protocolo previo](BIESTABLE_VENTANAS_ESTATICAS_PROTOCOLO.md), fijado en
`ae03ee2`, amplía las cuatro sondas a los 16 intervalos originales de cada
ventana. No añade solves no lineales ni cambia reloj, historias o integrador.
R61=200 Ω, BUS=0, KEY=10 V y cargas Q25/Q15 `finite_transit`, escala 1,
mantienen el alcance documental anterior. No hay referencia física.

## Resultado por ventana

Gate de mapa: máximo por componente de |X−XDecimal80|/(1+|XDecimal80|) <10⁻⁸.
Cada mapa tiene 94 nodos y 25 columnas de memoria.

| Ventana | Mixto histórico | Ordinario | Compensado | Máximo compensado |
| --- | --- | --- | --- | --- |
| Prefix | 6/16 | 14/16 | 16/16 | 1,18347×10⁻¹⁴ |
| Attack | 4/16 | 15/16 | 16/16 | 2,68322×10⁻¹⁴ |
| Reset | 4/16 | 13/16 | 16/16 | 2,79041×10⁻¹⁴ |
| Tail | 10/16 | 12/16 | 16/16 | 1,75273×10⁻¹⁴ |
| **Total** | **24/64** | **54/64** | **64/64** | **2,79041×10⁻¹⁴** |

Los diez fallos ordinarios permanecen completos; el máximo es
6,98084×10⁻⁷. La coincidencia en un primer intervalo no cubría los siguientes.
Las etiquetas heredadas `mixed_value` y `candidate_value` del helper de
comparación designan aquí referencia Decimal80 y candidato, respectivamente.

Pasan los **256 solves racionales** (cuatro rutas por intervalo), con residuo
racional exacto cero antes de redondear y ambos errores hacia atrás <10⁻¹⁰.
Máximo observado después de redondear: **1,87018×10⁻¹⁶**. Esta comprobación
algebraica no subsana un mapa ordinario o mixto que difiere de la referencia.

Las 64 corrientes originales frente al grafo Decimal pasan 10 pA, máximo
**1,46965×10⁻¹⁷ A**. Las 128 corrientes binary64 de las dos preparaciones
pasan, máximo **1,47410×10⁻¹⁷ A**. Sus 128 derivadas pasan el gate
10⁻³⁰ S +10⁻⁸|JDecimal80|; máximo error normalizado **3,59315×10⁻⁷**.

## Precisión Decimal y límites

Decimal80 y Decimal100 producen Jacobianos redondeados y mapas idénticos
en **64/64** intervalos. Sus residuales redondeados coinciden en **58/64**.
En attack, índices 3, 5, 11, 12, 13 y 15, la fila 33 del cursor de balance
queda en −10⁻⁸² A a precisión 80 y −10⁻¹⁰² A a precisión 100. La diferencia
es 9,9999999999999999999×10⁻⁸³ A: se conserva el indicador de no identidad,
sin recortar esos valores a cero ni convertir identidad en gate de corriente.
No demuestra residuo matemático exacto ni precisión infinita.

El grafo de audio está transcrito independientemente. Contorno, R59,
capacitancias y cargas permanecen compartidos. Estos resultados admiten
estudiar la [variante explícita del integrador](BIESTABLE_INTEGRADOR_COMPENSADO_PROTOCOLO.md)
en las mismas ventanas; aún no prueban acumulación no lineal, controlador
desde DC, gate temporal global de 1 mV, conmutación física, audio o deadline.

## Evidencia y validación

[Datos completos](../evidence/loudness_latch_bdf_static_precision_windows.json.gz):
**8.053.187 bytes**, SHA256 comprimido
`65480d19c9be037bb9ac2fa125b478523e235b14a4833da456e888a6fe9d9f2c`;
SHA256 JSON canónico
`ad50b64467688d1ab36a1b1bb273f89885701717de420359c1d17ed88eeefa95`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_windows_summary.json)
identifica **126 entradas**, constantes, matrices/contrastes por caso y
HEAD contextual `ae03ee2`. Sus SHA permanecen iguales antes/después.

El [recibo](../evidence/loudness_latch_bdf_static_precision_windows_validation.json)
registra **4/4 pruebas**, un intento exitoso, 53,4274 s y entradas intactas:
replay de 64 candidatos y derivadas independientes, 256 matrices/gates,
ocho solves racionales nuevos de control y almacenamiento/alcance. No se
repite ni se modifica la suite histórica.

`python tools/validate_bdf_static_precision_windows.py`
