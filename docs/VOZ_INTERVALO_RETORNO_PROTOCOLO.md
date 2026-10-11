# Un intervalo completo entre resets: respuesta de C27

Protocolo previo, 2026-10-10. Model D clásico CA3046, escena y biblioteca
intactas. Perfil memoria 0 / límite 125 ns de los ciclos corregidos.

## Dominio y salida

Desde la historia real anterior al bracket del primer reset hasta el final
del bracket del segundo: 22356 medios pasos del calendario registrado.
Se reproducen las siete tensiones de cada endpoint por bits y los cinco
estados HIGH/LOW de los cuatro pasos de ambos brackets seleccionados.
No se redefine el origen como el estado interpolado del primer evento.

Se propagan las nueve direcciones 43,5,12,139,199,194,157,117,98 con
el helper previamente admitido. Se observan ambos eventos con el mismo
interpolante/proyección de fase del bloque anterior. Salidas:
periodo observado T=t2-t1 y deriva de estado D=Z2-Z1;
`dT=dt2-dt1`, `dD=dZ2-dZ1`. Se conservan las 18 diferencias de tensión
de capacitores de cadena, C27 y J7, sin omitir empeoramientos.

Se contrasta el recorrido no lineal completo únicamente para la dirección
139 (entrada 6 de cadena): modifica inicialmente V(C27)=V139-V12 con BUS
y rampa iniciales fijos. No es la derivada respecto de una raíz condicionada
de las 18 cargas ni un mapa de Poincaré desde el primer estado interpolado.
Las otras ocho columnas se calculan como recurrencia nativa; no se promueven
como derivadas completas contrastadas por historias propias.

## Escala, contraste y gates

Primero recorrer toda la línea base y fijar un epsilon por dirección usando
el máximo cambio previsto de todas las etapas del intervalo: base 10 µV
o 0.1 nA, techo 10 µV / 10 nA. Después cuatro historias propias completas
para 139, ±epsilon y ±epsilon/2; calendario sin adaptación. 89424 nuevos
solves perturbados, además de 22356 de línea base. Ambos brackets de cada
historia deben mantenerse transversales y contener -2 V en sentido creciente.

Gate de cambio del estado en fase y deriva: 1e-8 V / 1e-11 A + 1e-4 relativo.
Gate de cambio de periodo: 1e-17 s + 1e-4 relativo. Para las diferencias de
tensión de ramas, 2e-8 V + 1e-4 relativo (suma de dos gates de nodos).
Restar tiempos de evento relativos a cada bracket; el tramo de ticks común
se cancela antes de medir la diferencia central de periodos.

Guardar 15 puntos preseleccionados: 0,1,2,64,256,1024,4096,8192,12288,
16384,20480,N-4,N-3,N-2,N-1. El oráculo reconstruye masa y Jacobiano
independientes en esos pasos y aplica la respuesta a la sensibilidad entrante
nativa. Es contraste de operadores seleccionados, no propagación independiente
de todos los pasos. El contraste completo de la columna 139 lo aportan las
cuatro historias no lineales. Sin nuevas raíces no lineales independientes.

Control algebraico 98: respuesta exactamente cero durante todos los pasos
y ambas proyecciones. Rampa proyectada escalada≤1e-18 V. Observador base
y perturbado: alpha≤2e-15 de error y estado≤1e-13 V / 1e-16 A frente a
Decimal100; sección -2 V con error≤1e-13 V. Los gates Newton quedan intactos.

## Recursos y decisiones

Salida compacta: traza de siete observaciones, 15 estados/sensibilidades,
brackets y eventos; no matrices por paso. Estimación 64 MiB, reserva 1 GiB,
pila 32 MiB y vigilancia 250 ms. Compilación≤120 s, ejecución≤2300 s,
éxito total≤2400 s; hasta 4800 s administrativos si se requiere replay de
un fallo. Guardar fuentes, parciales y replay antes de reparar. Verificador
≤300 s. Sin borrar evidencia ni recompilar biblioteca, audio o SPICE.

Admisión prevista: respuesta observada de T/D a perturbación inicial de
139 para ese intervalo y calendario. No acredita otras memorias/resoluciones,
las 18 direcciones de carga, evento continuo, calendario adaptativo,
periodicidad asentada, corrección periódica, fidelidad física ni tiempo real.
