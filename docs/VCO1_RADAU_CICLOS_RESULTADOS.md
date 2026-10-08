# VCO1: ciclos propios Radau y primera escucha nativa

2026-10-08, base4efd8b8. CA3046 clÃ¡sico nominal, 25 Â°C, C4=10 pF,
R8=0,5/R11=500 ohm, controles y mixer impuestos. [Protocolo](VCO1_RADAU_CICLOS_PROTOCOLO.md),
[recursos](VCO1_RADAU_CICLOS_EXTENSION_PROTOCOLO.md), [Newton local](VCO1_RADAU_NEWTON_PROTOCOLO.md),
[recuperaciÃ³n](VCO1_RADAU_RECUPERACION_PROTOCOLO.md), [conformidad](VCO1_RADAU_CONFORMIDAD_PROTOCOLO.md)
y [escucha](VCO1_RADAU_ESCUCHA_PROTOCOLO.md). No cambia el crate de producciÃ³n.

## Dos recorridos desde arranque propio

[Banco04](../evidence/voice_vco1_radau_cycles04.json): 30 ms en cada perfil,
desde semilla/raÃ­z de circuito, sin importar historia SPICE. C1=0 es la
condiciÃ³n inicial; su corriente se retira antes de integrar. Radau conserva
268 ecuaciones, cargas no lineales, hi/lo y flujos de ambos 741. Reloj u64,
tick=125 ns/65536; full/mid/end, gates y publicaciÃ³n atÃ³mica conservados.

| MÃ¡ximo aceptado | Endpoints | Frecuencia (Hz) | DispersiÃ³n relativa | Balance Qa/Q10/C1 |
|---|---:|---:|---:|---:|
| 250 ns | 153696 | 410.80175102836 | 1.8027e-11 | 3.7213e-06 |
| 125 ns | 272814 | 410.80175096891 | 4.9396e-10 | 3.5561e-06 |

Seis cruces tras 15 ms y cinco perÃ­odos asentados por perfil. Gates previos:
dispersiÃ³n <=1eâˆ’5, balance <=0,002, frecuencia <=1 cent, extremos <=5 mV.
ComparaciÃ³n250/125: **2.50532e-07 cent**, mÃ¡ximo de extremos
saw/tri/pulse **7.91926e-07 V**. El balance conserva su exclusiÃ³n de Q7 y
cuadratura. Frecuencia y reset salen del circuito; no hay reloj de ondas impuesto.

## Contrastes

Las corrientes transitorias usan F(Y2)âˆ’4,5Î”Q(Y1)/h+2,5Î”Q(Y2)/h; no una
diferencia Euler entre endpoints. Qa/Q10 colector, Q7 gate y panel conservan
signos/retornos. Ocho intervalos reales seleccionados aportan16 comparaciones
de etapas Decimal100 desde historia, sin semilla nativa;32 identidades de
puerto y32 corrientes, con el panel. No es una trayectoria independiente
completa ni una prueba de orden global en la DAE.

[Conformidad](../evidence/voice_vco1_radau_conformance01.json): cuatro parejas
con Gear2/Trap2 a125 ns archivados y validados, mismas fronteras nominales.
MÃ¡ximos **9.12897e-05 cent** y **3.03524e-06 V** de extremos. Cero nuevos
procesos SPICE; fase sÃ³lo diagnÃ³stica. No calibra CV/trims ni C4=100 pF.

## Fallos conservados y bÃºsqueda de Newton

[Banco01](../evidence/voice_vco1_radau_cycles01.json): compilaciÃ³n rechazada
por literal .03, original/replay sin fÃ­sica. [ReparaciÃ³n por bytes](../evidence/voice_vco1_radau_cycles_repair01.json).
[Banco02](../evidence/voice_vco1_radau_cycles02.json): interrupciÃ³n administrativa
por coste proyectado. Su adaptador rechazÃ³ una fila parcial; el
[recibo](../evidence/voice_vco1_radau_cycles_resource01.json) declara el tail
no recuperable y no infiere un rechazo elÃ©ctrico. Fuentes medidas y gzip
sobreviviente quedan conservados; [snapshot](../evidence/voice_vco1_radau_cycles_extension01.json).

[Banco03](../evidence/voice_vco1_radau_cycles03.json) completa250 y rechaza125
por LineSearch a12,171591857910155 ms. [DiagnÃ³stico local](../evidence/voice_vco1_radau_newton01.json):
original/replay reproducen full del trío8 ticks y mid del trío16 ticks rechazados. InstrumentaciÃ³n
muestra correcciÃ³n descendente y residual fuera de gate. Cambiar Ãºnicamente
Armijo a descenso del residual resuelve los tres trÃ­os8/16/32 ticks;
Decimal100 confirma error temporal0,0664105/0,257738/0,950213 <=1.
No se relaja ninguna tolerancia o presupuesto Newton64/24.

Son18 comparaciones independientes de etapas, **14 problemas de etapa Ãºnicos**:
full(h) y mid(2h) repiten ecuaciones/historia.42 comparaciones nativas incluyen
12 etapas instrumentadas repetidas; los replays se verifican sin sumarlos.
Esto recupera la tupla local; banco04 completa despuÃ©s el recorrido restante.

## Checkpoints y recursos

Banco04 hereda250 Ã­ntegro del banco03. Para125 conserva el prefijo completo
hasta el fallo y continÃºa desde hi/lo, tick y propuesta LTE. La integraciÃ³n,
fÃ­sica y gates son iguales; sÃ³lo cambia el mÃ©rito de bÃºsqueda en la continuaciÃ³n.
El recorrido250 tambiÃ©n verificÃ³ echo y una fila adicional por bytes al
continuar su prefijo administrativo; usa la bÃºsqueda original. Los streams
lÃ³gicos omiten sÃ³lo los echoes y no escriben otra copia grande concatenada.

Exports546 columnas, XOR/byte shuffle/gzip reversibles. Todos los stdout
nuevos pasan longitud/SHA al decodificar; para el prefijo administrativo se
verifica sÃ³lo lo conservado, no se atribuye un hash al flujo entero perdido.
El adaptador siguiente guarda tails parciales. Presupuesto2400 s/proceso,
reserva1 GiB monitoreada y pila8 MiB de laboratorio; coste real en recibos.
Esto no acredita heap, deadline o producciÃ³n. Los cambios de recursos y
fuentes previas se congelan antes de cada extensiÃ³n; no se reejecutan prefijos.

## Escucha del VCO nativo

[Recibo](../evidence/voice_vco1_radau_listening01.json): cuatro WAV privados en
artifacts/vco1-radau-native01. Sierra, triÃ¡ngulo y pulso,0,75 s cada uno;
montaje2,55 s con pausas0,15 s. Repite el Ãºltimo ciclo real del perfil125,
**410.801750926 Hz**; simula30 ms, no toda la duraciÃ³n del montaje.
Fourier del interpolante no uniforme, DC omitido, 52 armÃ³nicos
bajo0,45 Fs,48 kHz PCM16 mono,8 V/full scale fijo, fades10 ms. Sin normalizaciÃ³n
individual ni ondas analÃ­ticas. QA regenera coeficientes y PCM por bytes.
TodavÃ­a no incluye filtro/VCA o voz completa, ni identifica hardware vintage.

[QA](../evidence/voice_vco1_radau_cycles_tests01.json):235 tests Rust heredados
por identidad, cero nuevos/reejecutados. Contrastes de raÃ­z, replays, cÃ³dec y
WAV se cuentan por su tipo; unicidad por historia/dt canÃ³nicos. Fuentes y
hashes privados anteriores protegidos mediante snapshots. ProducciÃ³n/RT,
carga activa y escenas reservadas siguen pendientes.

Siguiente: motor portable y dominio temporal comÃºn con la cadena. Sus125 ns
actuales no cubren los mÃ­nimos del VCO; resolver esa brecha antes del mixer
activo y transferir R6/R45 una sola vez. Extender CV/trims y C4=100 pF bajo
sus propios bancos, sin sustituir modelos o tolerancias para obtener convergencia.
