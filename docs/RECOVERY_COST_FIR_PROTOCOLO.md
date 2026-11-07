# Leer el mismo FIR sin módulo en cada tap

Previo, 2026-11-06. Exponencial12 pasa las reservas y banco1200, pero
falla confirmación4800. Retener ambos bancos y el replay. No cambiar
la medida, el integrador, el solve ni sus fuentes después del rechazo.

Probar otra implementación de lectura del mismo anillo FIR. Dividir en
dos tramos contiguos en el punto de vuelta; recorrer los mismos769 taps,
muestras, productos y orden de suma. Guardas, latencia384 y reloj iguales.
El módulo se calcula una vez para el origen del anillo de cada frame;
suprimirlo del bucle de taps. No cambiar antialias ni plegar sumas.

Verificar voltajes por bits, índices, disponibilidad y contadores frente
al FIR congelado, bajo fragmentación no uniforme, entrada del núcleo
exponencial en tres puntos, e impulso con DC. Comprobar invalidación
atómica y cero heap. Reusar la admisión numérica del mismo kernel por
fuente/hashes; comprobar que este binario conserva los vectores por bits.

Banco1200 y confirmación4800 con reglas previas, mismo reloj/entrada,
cero heap y primer bloque. Conservar fallo/replay; no elegir mejor banco
ni atribuir un pico de pared a una causa sin medirla. Si también rechaza,
cerrar este bloque con ese límite y los resultados reales. Los recibos
siguen bajo10MiB sin QA: no duplicar streams idénticos o WAV.
