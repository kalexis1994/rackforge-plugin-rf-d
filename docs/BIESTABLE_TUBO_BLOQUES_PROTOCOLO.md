# Protocolo: comparación dirigida del primer tubo no lineal

Reutilizar intactos los estados reales, los tres radios, ocho celdas,
recintos medios, residuales e inversas certificadas del primer tubo.
No volver a resolver el circuito ni calcular precondicionadores.
Reconstruir las inversas exteriores desde su fórmula y verificar su
certificado anterior. Guardar SHA de cada matriz completa reutilizada.

## Banco fijo y anclajes

Partición de 25 cargas: audio 0..16; C10 17; C2 18; C4 19; C7 20;
junturas 21..24. Orden fijo de radios: 1e-7, 1e-6, 1e-5 V.
En cada radio ejecutar todos los modos en orden infinito, RMS de junturas,
cuadrático de junturas con incertidumbre dirigida/balanceada. Elegir el
primer par radio/modo que cierre. Conservar todos los resultados.

Los primeros cinco bloques usan el máximo de sus cotas iniciales reales.
En junturas, infinito usa máximo, RMS la raíz exterior de suma de cuadrados
sobre dos; cuadrático usa forma P sobre la caja simétrica de los cuatro
errores ponderados, dividida por 2a. La caja simétrica incluye el intervalo
firmado archivado pero puede ser más amplia; no se trata como error exacto.

## Métrica común y conversiones

Para cada radio formar la envolvente de los ocho generadores de junturas
A_J=-W_J*(Hmedio^-1)_JJ*W_J^-1. Un único candidato Lyapunov del centro,
normalizado trace(P)=4 y nearest-even diádico a 40 bits, como en el helper
existente. Registrar solve racional 10x10 y LDL exacta; conservar rechazo
si el candidato bruto o redondeado no es PD. La métrica queda fija durante
195,3125 ns completos, incluso si alguna cota de crecimiento es positiva.

Conservar la cota isotrópica y la dirigida por congruencia racional;
formar además radios dirigidos balanceados con pesos ceil40(sqrt(1/D)).
32 bisecciones LDL en cada etapa. Intersectar superiores de la MISMA
métrica en orden isotrópico, dirigido y balanceado. Cambiar acoplamientos,
forzamiento integrado y ganancias nodales según P y P^-1, con raíces
exteriores; no usar coeficientes de la norma infinita para salida cuadrática.
RMS conserva la parte simétrica firmada y su Gershgorin exterior.

## Propagación conocida y cierre

Propagar dos vectores separados: anclaje real y forcing. Usar kernels
positivos Metzler exteriores del helper fijo, 32 términos, cola y
escalado; guardar matrices de endpoint y picos. Aplicar el pico a toda
la carga L1 en su celda, incluyendo inyección tardía; conservar picos
nodales por nodo antes de maximizar. Sumar ambos componentes por nodo
para evitar sumar máximos de nodos distintos. Incluir también el error
nodal inicial del evento al evaluar el máximo final.

Cierre sólo si todos los recintos medios son invertibles y el máximo
nodal completo es estrictamente menor que el radio. Heredar continuación
implícita y dominio del protocolo anterior. Si no cierra, duración real
certificada cero. La mejora de una norma no prueba estabilidad del hardware.

Validar reproducción de 24 inversas y de todas las variantes, anclajes y
conversiones. Un sistema no lineal escalar de solución conocida debe
aceptar un tubo suficiente y rechazar uno pequeño. Un bloque antisimétrico
manufacturado debe exhibir la cancelación RMS; comprobar forcing tardío
y particiones inválidas. Congelar fuentes antes de medir, datos y pruebas
antes de validar; conservar cada intento y ampliar el corpus completo.
1 mV global, voz completa, física y deadline mantienen gates separados.
