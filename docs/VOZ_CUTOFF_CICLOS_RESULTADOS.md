# Cutoff abierto: ciclos propios de la cadena conjunta

2026-10-12. Model D CA3046, cutoff1/RANGE0,1/R61=200 Ω, OSC1 ON/alpha0,5,
otras entradas OFF y controles VCA=2 V. [Contrato previo](VOZ_CUTOFF_CICLOS_PROTOCOLO.md),
[inputs](../evidence/voice_cutoff_cycles_inputs01.json),
[nativo](../evidence/voice_cutoff_cycles_native01.json),
[oráculo](../evidence/voice_cutoff_cycles_reference02.json),
[escucha/decisión](../evidence/voice_cutoff_cycles_listening01.json),
[QA](../evidence/voice_cutoff_cycles_tests01.json).

## Continuidad física y reloj

Se continúa desde los finales abiertos propios a250 µs. El primer checkpoint
de cada extensión es idéntico por bytes al final correspondiente; la
receta reconstruye los parámetros con cutoff1. No se sustituyen cargas
por un nuevo DC ni una memoria de otro perfil. La unión conserva el
prefijo admitido sin reintegrarlo: recorrido total0→5,25 ms, dos resets
por perfil y un intervalo transitorio entre ellos. Veinticinco relojes
posteriores al inicial comparan estados completos a2 µV/2 nA.

El llamador elimina el solve startup VCO que scene calculaba y descartaba.
Las raíces iniciales nuevas **aplicadas a la trayectoria** son cero. El
prefijo corto invocaba una vez esa fábrica nativa por proceso (dos llamadas
en los perfiles abiertos heredados); su resultado no se usaba como seed.
Los helpers Python pueden calcular DC auxiliares para montar referencias;
no son búsquedas independientes de raíces iniciales/dinámicas del recorrido.
La sustitución declarada mantiene parámetros y deja el estado dummy sin uso.
No se presenta esa eliminación como una optimización de audio admitida.

## Intervalo observado

| Máximo h ns | Periodo ms | J7 mínimo V | J7 máximo V | Diferencia de extremos V | Diferencia/rango |
|---|---:|---:|---:|---:|---:|
| 125 | 2.43426399471 | -0.00231364082695 | 0.00322160067922 | 3.35424839e-05 | 0.00605980495 |
| 62.5 | 2.43426400628 | -0.00231364084572 | 0.00322160082689 | 3.35424908e-05 | 0.00605980601 |

Refinamiento de periodo 8.22919184e-06 cents (gate1).
Se detectan brackets propios y se verifica su pertenencia a medios pasos
seleccionados. Decimal100 observa estados, tiempos y derivas de18 ramas/J7;
la interpolación no sustituye una raíz sobre la superficie de evento.

| Rama | Deriva por fase125 ns V | Deriva por fase62,5 ns V |
|---|---:|---:|
| 0 | -0.000016637113830026167183644203709786901016602186795880328581014206324897761027101363729237968228904 | -0.000016637081944656031434986729358544283691247412906782863834813598182971478165746950179961903683710 |
| 1 | -0.000016700421816163854489738351570958028568103606479652325781746111938790916910108551851999573712936 | -0.000016700386441075424856558154288503264982694516211742602254366967968196143335977107645723882589730 |
| 2 | -0.000016768111342076221341389855906858550292793295235367149920463472330090831461682105430408108383328 | -0.000016768076065705931900218245003969637191280087694374104533959371755991958238814025696677551553039 |
| 3 | -0.000042896024387316048383459216975944421342495243502792205563041732504662746083674145873171696557155 | -0.000042895989236514845293092367350228775845374807973320295357720902780592217509309723128074172783090 |
| 4 | -0.000040230131865940484242083149175590521552983244506620309129901552055360909498800553802549413316030 | -0.000040230133286375035533857554864977579867168585883468095831370522966885708007257857298034241133874 |
| 5 | -0.000002269507929192138739856346720103315246945649647817231973904717052372140626513032021367889011895 | -0.000002269482061974510449114479995341748731383647062886593396297376757628204091246315125715740729866 |
| 6 | 0.013008544131115090033217948649603787308571357618262363003719524638223364376456854733674529192053302 | 0.013008544172867428744596344510826267987994160717664260500355293838238976867232496455711374966632232 |
| 7 | 0.013098691341559911645006505044871187266144401729591908830211882206809288933410645422476865128417330 | 0.013098691393970919029030178034411894598547778559282410054611920423424965522362829590518997393945296 |
| 8 | -0.000159046919180251889108684463289384498347381519738039265486444963185436179840572946833614998073263 | -0.000159046946938744226606922717734205551072258754824616751654640559215174435586547102746293779762765 |
| 9 | 0.001881984480640443209364186428995492042108030597531796233332824329272005585871452043751748908208743 | 0.001881984329060716945366853201217128489570138413809628646232512451353276914307410744009861952827999 |
| 10 | 0.000002079936841177007882550165980067644074757206088457660467884627801323766510428018576060796359956 | 0.000002079936618394081899941600688442577479023621752139896110675754851251587933415140491053502648065 |
| 11 | 6.01160276314219412211789558976451351861311673362714695910358149183692583513806296651603837001E-7 | 6.01160274514561151914841095659072275153751595674051908895232713278786894368851902628875957827E-7 |
| 12 | 0.000277606814512054416063244095088827005902964101646783329893694437879715484979115732746660313129692 | 0.000277606778651539885443378722864053274184220817602916762961789364261423513603079387126677127358914 |
| 13 | -0.000014415410226717449278839142636212495005421178375410427616311911783966340709170393691798627182603 | -0.000014415429836556143369890080178715354872832985480298183644198014031895102298489910929407905150522 |
| 14 | -0.000313325352184057308969445302559626264096365628599009816933485749174426922212757630161793684301956 | -0.000313325418452259833295501466789975357516091525333745209012764424542906455422552482784584807771875 |
| 15 | -0.000001807799379253984345876302568087661617719324936262869389132772603898410547763247116721905952858 | -0.000001807802669797711830488753109449938172970888832071201603592976862042446942742684457642222862517 |
| 16 | 0E-101 | 0E-101 |
| 17 | 0.000060521168495403308621227876228087516063790047536947755123177976847526588441779138529160199607904 | 0.000060521165958131306033730421624945409030882474525373941079272185721284676032349201496439356777570 |

Los cambios no se etiquetan como periodicidad asintótica. PLUS/masa se
identifican y cancelan en diferencias de rama. Se conservan estados al
mismo reloj, el cambio de salida y las cargas de la escena abierta.

## Conservación y cobertura

138 candidatos/55200 ecuaciones nuevas,92 observaciones de corrientes VCO,
46 LTE y cuatro restores nuevos por bits, a250 µs/2,5 ms. El prefijo hereda
su auditoría y dos restores por perfil por identidad. El código de referencia
con globals aislados conserva la KCL y gates de la escena cutoff1.
No se afirma integración independiente de todas las etapas.
El intento01 del auditor falló por un import D faltante; fuente, excepción
y repetición sin cambios quedaron en el [recibo rechazado](../evidence/voice_cutoff_cycles_reference01.json).
El intento02 añade ese import y numeración de intento, sin cambiar el cuerpo
del auditor, gates o datos nativos. La publicación verifica esa reparación.

C18/cola por checkpoints y ledger nativo de etapas en20 relojes nuevos;
balances C18/C1/C27 tanto por segmento como por recorrido completo,
sumando integrales sin duplicar la frontera. Las medias Radau del panel
mantienen sus identidades. KCL≤1e−12 A, C18/C27≤1e−12 A·duración,
C1≤0,002, sin cambios de gates. Dos calendarios adaptativos propios.

## Decisión de escucha

Se admite la escucha del intervalo observado, repetido por el adaptador.
Gate de seam≤1 % del rango en ambos perfiles. RMS de armónicos alineados
en fase: error 8.11727477e-11 V,
gate 1.58470261e-05 V. La comparación excluye DC;
frecuencia y offset se publican por separado, no se normalizan para pasar.

WAV de inspección: `artifacts/cutoff-open-native01/rf-d-j7-cutoff-abierto-inspeccion.wav` (privado), 2 s/48 kHz/PCM16,
100 mV/full scale fijo, magnificación80× respecto del adaptador8 V/FS,
sin normalización individual ni clipping; DC retirado -4.56564241585e-06 V.
Sólo se simularon5,25 ms por perfil. La salida repite el intervalo entre
dos cruces del perfil62,5 ns, con armónicos hasta0,45 Fs y fades10 ms.
Coeficientes recalculados por bits y payload PCM verificado de96000 frames.
No equivale a2 s de circuito, una escala de producto o voz con contornos.
La salida observada es J7 con cargas tip/ring32 Ω cada una, R21 inferior
2000 Ω; el panel mantiene R20 inferior2500 Ω, Hi10 kΩ y Lo100 kΩ. Se
heredan estas fronteras del helper congelado, no un nivel de línea vintage.

## Recursos y alcance

Nativo 1687.032649 s, auditor 51.775043 s,
salidas 34496673 bytes. Dos procesos, stacks32 MiB,
RAM inicial≥1 GiB, reserva disco1 GiB, estimación64 MiB. Compile≤120 s,
perfil≤2400 s/60000 intervalos, éxito≤2600 s, administrativo≤3200 s,
auditor≤300 s. Biblioteca congelada y248 tests heredados por identidad.
Sin nueva biblioteca/SPICE, fidelidad física o RT. El banco admite la
ventana/controles observados; VCO2/3, contornos y producto siguen abiertos.
