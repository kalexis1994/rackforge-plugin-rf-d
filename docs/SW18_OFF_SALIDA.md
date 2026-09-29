# SW18 OFF: carga del VOLUME y salidas HI/LO

En **SVC-9 Fig. 9-17, PDF p. 19** (SVC-204D PDF p. 75), las secciones 5/2 de SW18 comparten el cursor de R20 VOLUME. En **ON**, los contactos 6/3 unen ese cursor a J4 HI. En **OFF**, 4/1 lo unen a masa. [La transcripción](../evidence/output_panel_hi_lo.json) mantiene ambas conexiones distintas.

Con `R20_inferior=r` y `R20_total=5000 Ω`, el pin 21 de placa 4 ve en OFF sólo `R20_superior=5000−r` hacia masa, después de R75 `1 kΩ`. La mitad inferior de R20 queda conectada entre dos masas. J4 HI queda desacoplado de R20, pero su nodo y J5 LO conservan R57 `33 kΩ`, R58 `1 kΩ` y las cargas externas impuestas. Por eso sus voltajes AC y temporales son cero en este circuito sin otras fuentes. La rama paralela R77/pin22/[R21](SALIDA_AURICULARES_R21.md) sigue cargando C2_RIGHT.

La [matriz AC explícita de 53 nodos](../tools/filter_panel_headphone_reference.py) cambia sólo los estampados de contacto y conserva C2/C4, los dos VCA y las redes del filtro. Su equivalente resistivo visto desde C2_RIGHT es `R75+R20_superior`, en paralelo con `R77+R21_superior+(R21_inferior∥Z_cursor)`. El [paso no lineal](../tools/filter_panel_headphone_reference.py) usa exactamente esas cargas en el estado de 48 nodos y reconstruye el pin 21. Las [pruebas](../tests/test_filter_panel_headphone_reference.py) comparan el resultado OFF con el oráculo reducido, confirman el aislamiento HI/LO y verifican corrientes y KCL.

Esto describe contactos nominales, no fuga de interruptor, transitorios al conmutar, contactos de jacks ni una posible señal inyectada desde otro cableado. Las posiciones eléctricas de R20/R21, las cargas externas y el modelo de semiconductores continúan condicionados.
