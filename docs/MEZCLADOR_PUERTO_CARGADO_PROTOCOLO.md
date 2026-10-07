# Puerto cargado de cinco fuentes: protocolo previo

El cierre ON/C27→J7 admite cuatro escenas con generadores impuestos.
Para sustituirlos por VCO reales hace falta entregar la corriente vista
por cada fuente y su tangente con toda la cadena ya cargada. Conservar
red nominal SVC-9 pp.19/13/10, ambos R61 e hipótesis del banco anterior.

`solve_input_port` toma estado anterior inmutable y tensiones OSC1/2/3,
NOISE/EXT, y devuelve un candidato completo, cinco corrientes entrantes,
matriz 5×5 y gradientes de los 66 nodos y BUS. Nunca confirma histories.
El Jacobiano del sistema admitido resuelve cinco RHS: únicamente fila6
recibe `−di_BASE/dsource`. La tangente de corriente de fuente combina el
stamp reducido y la respuesta BASE_Q29 de la cadena. La red activa posterior
no obliga a que esa matriz cargada sea recíproca o pasiva.

## Gates fijados antes del ensayo

Cuatro estados no triviales (paso3 del oráculo ON/C27→J7): ambos R61,
sólo OSC1/cinco ON. Python conserva BUS/cursores como incógnitas, historia
original fija y fuentes desplazadas ±1 mV; vuelve a resolver todos los nodos.
No usa el Jacobiano Rust ni sus raíces como semillas. Comparar las cinco
columnas de corriente: <1e−8 S+1e−3·|Y_fd|; 66 nodos y BUS:
<1e−6 V/V+1e−3·|dx_fd|. Corrientes y candidato central mantienen los
gates de la cadena. Fuentes omitidas no afectan nodos ni otras corrientes.

Repetir calls con entrada idéntica debe conservar todos los bits de estado
del llamador y del candidato. Un rechazo no publica nada. Medir cero heap
en 16 solves/tangentes completos en un test aislado; no acreditar deadline.
Compilar biblioteca real, conservar hashes/commands/binarios y todos los
fallos. No más SPICE, física nueva, audio ni integración de VCO por este puerto.
