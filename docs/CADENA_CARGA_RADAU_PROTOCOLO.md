# Cadena con cargas explícitas: protocolo previo

Paso hacia el cierre VCO→mixer→ladder→VCAs→J7. Las fuentes siguen impuestas
en este banco. No se declara realimentación eléctrica al VCO ni voz completa.
SVC-9 PDF pp.19/13/10; hipótesis nominales de `circuit66` y del puerto ON.
Conservar ambos R61 documentales y las tarjetas anteriores. No agregar
cargas de juntura a los BJT de la cadena: ese modelo anterior es condicional.

## Derivación

68 tensiones hi/lo: 66 nodos anteriores, BUS explícito y nodo izquierdo
de C10. F procede de `circuit66::linearize_dc` y la red ON; 17 capacitores
con incidencias originales, C27 entre BASE_Q29 y BUS, C10=10 µF entre
su nodo izquierdo y BASE_Q30. Resistencia serie C10: R14+1330−R30 ohm.
R14 abierto: memoria C10 fuera del circuito, coordenada auxiliar igual a
BASE_Q30. Serie cero: contacto exacto, auxiliar igual al nodo22 y C10
directo entre22/7. Sin resistencia epsilon. R21 conserva igualdad de
voltaje en fila49 y suma KCL en fila48 al extremo superior.

Q/h se construye desde incrementos de tensiones, nunca por restar dos
stamps que contienen C/dt grande. F(hi)+Jdc(hi)·lo y Jacobiano DC de hi:
mismo contrato de primer orden/quasi-Newton del VCO. Sin eliminación de
C27 ni actualización de memoria durante Newton. Fronteras y fuentes
constantes durante cada paso; no se admite cambio de alimentación o pot
a mitad del intervalo. Fuente al panel ON posee su carga una sola vez;
transferir R6/R45 del VCO sigue pendiente del cierre conjunto.

Radau IIA de dos etapas sobre F y Q: mismo A inverso que el VCO,
B=[[1,5;0,5],[-4,5;2,5]], endpoint igual a última etapa. Newton64/24,
residual <=1e-13 A o1e-11 V en restricciones, corrección <=2e-9 V.
Máximo1 ms; mínimo4 ticks del VCO (125 ns/65536 por tick).
No se amplía el contrato de los antiguos módulos Euler/directos.

## Banco y gates

Doce escenas: R61=200/200000 ohm, una/cinco fuentes ON, intervalos
125 ns,31,25 ns y15,2587890625 ps. Historia de nodos de paso3 del banco
independiente anterior a125 ns, BUS y C10 explícitos. Cada escena resuelve
full/mid/end; en el mínimo full usar8 ticks, medios4. Python monta F
desde el oráculo nodal anterior, red BUS/cursores sin reducir y cargas
explícitas; FD de DC, incidencia analítica de C. Coordenadas de incremento
para evitar perder carga al formar tensiones absolutas. Binary64 físico y
álgebra NumPy, no Decimal100. Semilla cero en incrementos, sin raíces Rust.

Comparar todas las etapas <=1e-6 V y corrientes fuente <=1e-9 A.
Error full−end sin dividir:2 µV; medirlo y exigir<=1 para admisión temporal
local. Contrastar Jacobiano completo a historia fija, tolerancia
1e-8+2e-5·abs(FD) S, restricciones en V/V. Contrastar el stamp Euler
en125 ns con el módulo anterior para conectar ambas formulaciones;
gate2e-10 A, igualdad1e-11 V. Verificar contactos R21/C10 y ausencia de
memoria dinámica en filas de igualdad; no admitir eventos por estas pruebas.
Medir heap en solves aceptados y rechazos; pruebas/fixtures fuera del conteo.

Preservar cada intento, fuentes, comandos y replay antes de reparar.
GNU fijado/O2, pila de laboratorio8 MiB, proceso900 s, reserva1 GiB más
estimación128 MiB. Tests previos239 heredados por identidad. No audio,
SPICE, campaña larga, calibración física, contornos libres o RT nuevos.
