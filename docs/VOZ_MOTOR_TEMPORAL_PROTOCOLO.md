# Motor temporal de la voz condicionada

2026-10-08. Extensión del [circuito conjunto](VOZ_BUS_CONJUNTO_PROTOCOLO.md).
Revisión CA3046 clásica SVC-9 pp.5/19/13/10, tarjetas nominales25 °C.
Sin nuevos dispositivos, componentes, compensación sonora o ajuste físico.

## Contrato previo a las mediciones

Estado200 high/low, parámetros eléctricos constantes, ajustes, propuesta y
reloj u64 integran el checkpoint. Restore valida representación y dominio;
no certifica procedencia física. La inicialización recibe la historia
condicionada del bloque previo; no simula un arranque conjunto desde DC propio.

Tick heredado:125 ns/65536 =1,9073486328125 ps. Frontera de par: múltiplos
de8 ticks; medio paso mínimo4 ticks. Propuesta: potencia de2, mínimo8,
máximo dos veces el medio paso máximo configurado (potencia de2 entre4 y
131072 ticks). Nunca sobrepasar el objetivo; el reloj solo avanza tras éxito.
Presupuesto1..20 intentos por llamada. No hay bucle temporal oculto en advance.

En cada intento, resolver desde la misma historia: un paso de2h y dos deh.
Publicar el endpoint del segundo medio paso, sin Richardson. Comparar las
200 coordenadas con diferencia compensada; puerta2e-6 V para tensiones y
2e-9 A para las35 corrientes MNA. Son tolerancias numéricas heredadas del
motor VCO, no umbrales de fidelidad. Error máximo normalizado <=1 para aceptar;
doblar propuesta si <=0,25, respetando el máximo. Rechazo: dividir por2.
Newton conserva64/24 y puertas del circuito conjunto. Un error preserva
memoria, controles, propuesta y reloj; tampoco publica un punto medio.

Observaciones antes de publicar: sierra, rampa, cursor, BUS, J7=cadena61,
corriente de R6 alta y serie33 kΩ. C27 usa la derivada Radau de sus
incrementos de rama, no diferencia Euler de endpoints. BUS debe cerrar
R45 + otras ramas impuestas + C27, tolerancia1e-12 A en el banco nominal.

## Banco definido

- Trayectorias hasta2 µs (1048576 ticks), otros puertos omitidos o impuestos
  como en el bloque conjunto; dos máximos de medio paso125 y62,5 ns.
- Límite4096 pares aceptados por trayectoria. Comparación al mismo reloj:
  2e-6 V/2e-9 A para todas las coordenadas. El control LTE es local y su
  acumulación debe medirse; no constituye una cota continua.
- Restore a mitad de recorrido y replay exacto de estados high/low,
  relojes, propuestas, intentos y métricas siguientes.
- Rechazos por reloj, presupuesto y representación; captura/replay de
  cualquier fallo antes de modificar algoritmo o escena.
- Contraste independiente de residuos/correcciones en etapas seleccionadas
  del comienzo y final, con el oráculo nodal del bloque previo y sus puertas.
  Puntos nativos declarados; no cuentan como raíces independientes.
- Heap medido en una aceptación y un rechazo concretos; stack de laboratorio
 32 MiB, tiempos de ejecución registrados sin declaración RT.

No se presupone que2 µs alcancen ciclo completo, reset del oscilador, señal
audible útil ni una nota musical. El resultado determina la próxima ampliación.
