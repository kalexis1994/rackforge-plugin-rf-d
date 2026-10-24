# Coordenada de C27 con transformación de puerto exacta

Decisión previa. Gear62.5 y Trap125 también abortan en -1.6/L1, antes
de 15 ms. No ampliar la campaña mediante más reducciones de paso.
La hipótesis siguiente cambia la representación de la carga, no C27.

Elegir K=.01, z=BUS/K (BASE=0), Cestado=C27*K²=1 nF.
Ecap impone BUS-BASE=K*z; una fuente controlada devuelve -K*I(Ecap)
desde z a tierra. KCL de z: Cestado*dz/dt-K*I(Ecap)=0, por lo que
I(Ecap)=C27*d(BUS-BASE)/dt. Carga física=Cestado*z/K y energía
=Cestado*z²/2=C27*(BUS-BASE)²/2. La potencia transferida por E/F
se cancela. Inicialización z=BUS_inicial/K, mismo estado físico.

No modificar dispositivos activos, resistencias, corriente de BASE,
tolerancias, duración o gates. Conservar retornos y signos. El control
previo -2.6/L1 debe completar 30 ms y coincidir con su representación
directa bajo todos los gates de frecuencia, ondas, BUS y corrientes.
Después evaluar -1.6/L1. Una convergencia distinta es resultado numérico;
no implica que la representación directa tenga otra física.

Si el control o el objetivo falla, conservar fuente/deck/log y replay,
sin admitir ese recorrido. Las ventanas/packs ya válidos siguen por hash.
