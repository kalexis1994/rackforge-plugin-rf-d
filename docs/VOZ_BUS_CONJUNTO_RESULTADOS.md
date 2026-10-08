# Cierre eléctrico local VCO1→BUS→cadena

2026-10-08. [Protocolo previo](VOZ_BUS_CONJUNTO_PROTOCOLO.md).
[QA](../evidence/voice_joint_tests01.json).

## Implementación

`joint_voice` une200 coordenadas eléctricas y400 ecuaciones de etapa.
Elimina solamente la corriente/fila/columna de VMIXER y comparte BUS12/66.
R6 y la serie de33 kΩ pertenecen al VCO; OSC1 está excluido del puerto
reducido. C27 pertenece a la cadena. El cursor permanece como nodo físico.
Las dos etapas se resuelven juntas y se devuelven como un solo candidato,
con high/low para memoria e incrementos. No existe aún un motor temporal
con publicación, reloj, checkpoint y rechazo por LTE de esta voz.

Se conservan modelos, revisión y parámetros nominales. El helper VCO es
aditivo; no cambia los módulos admitidos ni las funciones físicas heredadas.
La raíz VCO inicial fuerza C1=0. La historia de cadena viene del banco
independiente anterior; al levantarla, su BUS toma el valor histórico VCO.
Esta elección condicionada no demuestra arranque propio de la voz.

## Mediciones

Dos tests Rust pasan con compilador GNU fijado y stack de laboratorio32 MiB:

| Comprobación | Resultado |
|---|---|
| Dos configuraciones de puertos ×125 ns/7,629 ps | Cuatro pasos, ocho etapas acopladas |
| Residuo y corrección Newton | Puertas originales <=1 |
| Regresión de matrices de bloques | 640.000 entradas; prueba estructural |
| Diferencias centrales en BUS/cursor/sierra/C27/C10 | 40 columnas,16.000 entradas; peor fracción de puerta7,401e-5 |
| R45, cursor y C27 | KCL y acoplamientos con incidencia única |
| Rechazo h=0 | Cuatro llamadas; entrada por valor preservada |

El [oráculo nodal](../tools/check_joint_reference.py) evalúa los candidatos
nativos, deliberadamente: no obtiene raíces independientes desde otra semilla.
Usa VCO Decimal100 con voltajes y cargas sin redondeo previo; cadena Python,
Jacobiano por diferencias y cargas lineales Decimal. Comprueba1.600 filas
de etapa y resuelve una corrección lineal del sistema conjunto.
Puertas declaradas en el script antes de ejecutar:2e-11 A/2e-10 V de residuo
(contraste heredado VCO),1e-6 V/1e-9 A de corrección del oráculo.
Estas puertas de contraste no sustituyen las más estrictas de Newton nativo.

La peor fracción de puerta residual es8,581e-4; la mayor corrección del
oráculo es3,307e-12 V y7,399e-16 A. Se conserva el
[recibo completo](../evidence/voice_joint_reference02.json).

## Fallos preservados

1. La primera comparación estructural conservaba I(VMIXER) del arranque
   impuesto, aunque el stamp conjunto la eliminaba correctamente. Un test
   pasó y otro falló, con replay. Se corrigió solo la referencia del test.
2. El parser del oráculo omitió la primera escena porque el harness Rust
   anteponía el nombre del test al marcador. Falló con replay; se corrigió
   el encuadre del marcador sin modificar valores o puertas.

Recibos, fuentes anteriores y binarios privados permanecen íntegros.

## Alcance pendiente

Estos pasos muestran carga activa local y cierre simultáneo, con controles
fijos y otros cuatro generadores impuestos u omitidos. No admiten todavía
una trayectoria acoplada, osciladores2/3, contornos activos, error temporal,
nota completa, fidelidad vintage ni tiempo real. No se midió heap en este
bloque; no se hereda esa medición de los solvers aislados. No hay nuevo audio
ni procesos SPICE. Siguiente bloque: motor conjunto con comparación
paso/medios pasos, rollback y trayectoria corta con historia propia.
