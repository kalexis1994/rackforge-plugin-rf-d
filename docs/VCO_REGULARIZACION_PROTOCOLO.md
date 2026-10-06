# VCO aislado: regularización numérica decreciente

La [representación JFET](JFET_RESET_REPRESENTACION_PROTOCOLO.md) pasa el
banco terminal pero rechaza el control VCO a 2.277410733 ms. Su log señala
el nodo interno xic3.4. Se conserva esa representación como diagnóstico;
el nuevo ensayo usa **las primitivas JFET y tarjetas originales**.

`rshunt` agrega conductancia a masa en todos los nodos analógicos, también
internos de macromodelos. Es una alteración de las ecuaciones, no un
componente identificado del sinte. El
[manual ngspice 46, página 318, sección 11.1.2.1](https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf)
describe la opción y resistencias >=1 Gohm para estudiar condicionamiento.
No se atribuye nuestro fallo a un nodo flotante sin evidencia adicional.

## Serie y gates congelados

1 Gohm, 10 Gohm, 100 Gohm: conductancias añadidas 1 nS, .1 nS, .01 nS.
No se prueban otros valores para elegir uno favorable. A cada nivel se
ejecuta primero el VCO de BUS=0 ya aceptado y luego el deck fallido de BUS
variable de la tercera iteración. Se exige identidad de ambos originales.
Duración 40 ms, máximo 500 ns, Gear2/KLU y tolerancias originales.

Control: voltajes <=5 mV en grilla común 5 microsegundos sin alineación,
frecuencia <=1 cent, mismo número de cruces de rampa -2 V y diferencia
temporal <=10 ns. Si todos los solves completan, ambos contrastes
sucesivos bajo BUS variable deben cumplir esos mismos gates.
Un rechazo detiene la serie. No se declara convergencia a conductancia
cero ni se selecciona automáticamente un valor para el modelo.

Esto sigue siendo VCO con frontera BUS impuesta de un experimento previo;
no cierra R45. Para admitir una aproximación posterior se necesitarán
cierre eléctrico, refinamiento temporal y contraste de la unión con los
mismos controles. La tarjeta E402, el 741 privado y todos los capacitores
permanecen idénticos. Las cargas añadidas se registran por separado.

Se excluyen decks con `C... Q=`: `rshunt` también cargaría sus nodos
generados de estado, como explica el
[reporte primario ngspice 848](https://sourceforge.net/p/ngspice/bugs/848/).
No se combina este ensayo con la transformación previa de cargas JFET.
