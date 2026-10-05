# Reset VCO: separar carga eléctrica y reloj numérico

Fecha: 2026-10-05. Referencia inicial: 78c0e0f. Cinco intentos de unión
VCO1/placa 4 fallan durante el primer reset; no se identifica todavía
una conexión física incorrecta ni se declara una limitación física del E402.

Se congelan seis intervenciones a 10 ms, Gear2 máximo 500 ns, con tarjetas,
trims, rieles y tolerancias anteriores. itl4=100 y bypass=0 se aplican a
todos los casos. Ninguna intervención se propone como circuito final:

1. VCO aislado, BUS fijado a cero: control positivo.
2. VCO con carga resistiva 470 ohm en BUS.
3. VCO con 10 microfarad en serie hacia carga 470 ohm y bias ideal 2 V.
4. VCO y placa 4 en el mismo solve, desacoplados por dos fuentes ideales
   de BUS=0 V. Comparten rieles ideales y reloj del solver.
5. Igual que 4 retirando sólo los capacitores discretos de placa 4.
   Permanecen las cargas de juntura de sus BJT: diagnóstico de memoria.
6. Unión completa anterior: control negativo reproducido con esta fuente.

Registrar reloj final, logs, exports y hashes antes/después. La finitud
de una traza parcial no admite la escena. Una vez aislada la causa, la
unión final debe pasar el [protocolo previo](VOZ_CIRCUITO_PROTOCOLO.md)
con circuitos y cargas completos; no se promueve una intervención.

Que falle el caso desacoplado refutaría una atribución exclusiva a la
carga del mixer. Si quitar capacitores cambia la conclusión, revisar
truncamiento, escala y publicación del solver antes de cambiar componentes.
