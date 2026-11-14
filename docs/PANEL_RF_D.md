# Panel de RF-D y conexiones del Model D

## Referencias visuales

El recorte frontal del Buffalo Museum of Science fija las cinco
secciones, los mandos de cada fila, los selectores con seis posiciones
y el código de color de los interruptores. La trasera de la unidad
6675 aclara las etiquetas LO/HI, Loudness, Filter, Oscillator y
S-Trigger. El detalle de la unidad de 1974 muestra la ubicación de
los dos jacks de pedal junto a las ruedas. Las imágenes de referencia
se conservan localmente en `references-local/model-d-panel/`.

| Vista | Fuente | Archivo local |
| --- | --- | --- |
| Frontal de la unidad del museo | [Alex Harden, recorte de Clusternote, CC BY 2.0](https://commons.wikimedia.org/wiki/File:Minimoog_panel.jpg) | `frontal-buffalo.jpg` |
| Trasera de la unidad 6675 restaurada | [Soundgas](https://soundgas.com/products/moog-1975-minimoog-model-d-6675) | `trasera-soundgas.png` |
| Ruedas y pedales de un Model D de 1974 | [Found Sound](https://foundsound.com.au/products/32255) | `ruedas-found-sound.jpg` |
| Vista superior del bloque izquierdo con las dos tomas y sus switches | [Tone Tweakers, Model D de producción tardía](https://tonetweakers.com/products/moog-minimoog-model-d-late-sn) | `izquierda-tone-tweakers-tardia.jpg` |
| Detalle oblicuo de las ruedas lisas y la placa de pedales | [Matrixsynth, fotos de la unidad 3362 de 1973](https://www.matrixsynth.com/2014/05/vintage-1973-minimoog-model-d.html) | `izquierda-matrixsynth-3362.jpg` |
| Detalle del dentado de las ruedas en una unidad tardía | [Eastside Music Supply, unidad 12807](https://eastsidemusicsupply.com/products/moog-model-d) | `izquierda-eastside-12807.jpg` |
| Izquierda de la trasera con las dos tomas de alimentación y EXT/LO/HI | [Echo Tone, Model D de alrededor de 1974](https://echotone.com.au/products/c1974-moog-minimoog-model-d-analogue-synthesizer) | `trasera-izquierda-echotone-1974.jpg` |

RF-D usa SVG para las piezas, las escalas, las formas de onda y
los jacks, HTML para operar los controles y CSS para el acabado y
las columnas adaptables. De RF-5 toma el mapa por función, los
rangos nativos con arrastre vertical, la actualización por parámetro
y los puntos de enlace MIDI del host. Los índices, rangos y tipos
del panel vienen del esquema público del perfil compilado.

Los interruptores horizontales serigrafiados llevan **ON** en el
extremo derecho. **Keyboard Control 1** conserva la marca encima y
**2** debajo. **Osc. 3 Control** gira en vertical con **ON** arriba.
**White/Pink** también es vertical y marca ambos tipos de ruido.
El control virtual de **S-Trigger** indica el cierre del contacto.
La sección lateral de la tecla es circular con un sector abierto hacia
afuera. Las dos caras planas del sector son las superficies de presión
y se encuentran en un valle. Solo se dibujan los hombros redondos
expuestos por encima del marco.
El SVG proyecta esas superficies con una cámara
ortográfica inclinada 21° hacia el borde inferior del panel. El foco
está arriba a la izquierda, a 225° desde la derecha en coordenadas SVG
y 36° sobre el plano. La orientación y la basculación se aplican antes
de proyectar y calcular los reflejos. El marco, el grano y la luz de
fondo siguen esa dirección. Las demás piezas conservan sus relieves
dibujados en SVG.
Los knobs y selectores tienen tapas de metal cepillado con un reflejo
fijo arriba a la izquierda. El indicador gira con el valor del control.
En escritorio, las líneas se interrumpen bajo **Oscillator Modulation**
entre Controllers y Oscillator Bank, y bajo **Filter Modulation** y
**Keyboard Control** entre Mixer y Modifiers. En la vista compacta,
estos controles quedan dentro de sus secciones.
[Manual temprano de Moog, pp. PDF 4–12](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=4) ·
[Frontal del Model D](https://commons.wikimedia.org/wiki/File:Minimoog_panel.jpg).

En el mixer, cada par de volumen y switch de oscilador comparte su
identificación. El indicador **Overload** está junto a **External Input
Volume** y responde al nivel del preamplificador. El selector **White/Pink**
queda junto a **Noise Volume**.

## Modificadores

| Parte del Model D | Función expuesta en RF-D |
| --- | --- |
| Controllers, OP-EARLY pp. PDF 7–8 | Tune, tiempo de Glide, mezcla OSC3/ruido y switch de modulación de oscilador. El bloque izquierdo reúne los switches, jacks y ruedas. |
| Oscillator Bank, OP-EARLY pp. PDF 6–7 | Rango y seis formas por oscilador, frecuencia relativa de OSC2/3 y switch OSC3 Control. El segundo selector de forma de OSC3 es la sierra invertida. |
| Mixer, OP-EARLY p. PDF 9 | Nivel y entrada/salida de mezcla para OSC1, OSC2, OSC3, ruido y audio externo. Blanco/rosa y luz de sobrecarga. |
| Filter, OP-EARLY pp. PDF 10–12 | Cutoff, Emphasis, Amount of Contour, Filter Modulation, tracking de ⅓ y ⅔. Los dos switches de tracking suman el seguimiento completo. |
| Filter Contour y Loudness Contour, OP-EARLY pp. PDF 10–13 | Attack, Decay y Sustain por contorno. Decay de la mano izquierda controla la caída final compartida. |
| Output, OP-EARLY pp. PDF 4–5 | Volumen principal, Main Output, A-440 y volumen de auriculares. El ciclo de vida de la instancia lo gobierna RackForge. |

Las ruedas **Pitch** y **Mod** reproducen el plástico marfil liso,
la hendidura para el dedo y la ranura estrecha de las unidades de 1973
y 1974. Al girarlas, la hendidura acompaña la curvatura de la rueda.
Se pueden arrastrar en pantalla y se actualizan con Pitch Bend y CC1
de MIDI. El **Pitch** virtual vuelve al centro al soltar el gesto,
como la rueda con resorte de la reedición de 2022. **Mod** mantiene su
posición. Los mensajes de Pitch Bend externos conservan el valor
enviado por el controlador. [Moog sobre la rueda de la reedición](https://moogmusic-help.freshdesk.com/en/support/solutions/articles/69000840518-moog-minimoog-model-d-what-are-the-differences-between-the-2022-and-the-2016-minimoog-model-d-).

## Jacks y enlaces

En **PLAY**, una vira de madera separa los mandos del bloque inferior.
Las ruedas, los switches y los pedales quedan a la izquierda.
**Connections** se mantiene visible sobre una placa de aluminio a la
derecha. En pantallas angostas, la placa queda debajo de las ruedas.

| Conexión histórica | Ruta en RF-D |
| --- | --- |
| J6 External Signal Input | El bus mono **External Input** del Rack alimenta el preamplificador. External On y External Level gobiernan la rama. En Connections, **EXT** recibe el cable de realimentación. |
| J4 HI, J5 LO y J7 Phones | Los tres jacks seleccionan qué señal va al bus principal estéreo de RackForge. La elección es excluyente. Main Output gobierna HI/LO y el volumen Phones actúa en su rama. |
| J1 Oscillator, J2 Filter, J3 Loudness | Parámetros en voltios, ajustables desde el panel y enlazables por automatización o MIDI. |
| SO-1 External S-Trigger | Entrada lógica que representa el cierre a masa y mantiene los dos contornos. Puede enlazarse a un pedal MIDI. |
| J1402 Glide y J1401 Decay | Jacks S-260 con contacto normalmente cerrado y estado independiente del switch. Mantener pulsado el jack o enviar un pedal por MIDI abre el contacto. **Resistive Pedals** mantiene ambas resistencias en MΩ visibles debajo de las ruedas. |
| Dos tomas auxiliares de alimentación regulada ±10 V | Alimentan accesorios analógicos en el original y quedan fuera del ruteo de RackForge. |
| Cable J5 LO → J6 External | En **Connections**, tocar ambos jacks o arrastrar de uno al otro. Tocar una punta conectada o soltarla fuera del destino desconecta el lazo. Escape cancela el gesto y recupera el cable conectado. El lazo cambia la fuente del preamplificador y External On conecta la rama al mixer. |

Para enlazar desde el panel, usar el menú de RackForge con clic derecho
o pulsación larga táctil sobre el mando, la rueda o el jack. **MIDI Learn**
permite guardar la asignación en el mapa del controlador o en la sesión
según el destino elegido en RackForge. Una pulsación sostenida táctil
sobre Glide Pedal o Decay Pedal abre ese menú. Tocá brevemente para
enviar un pulso, o desplazá el dedo mientras lo sostenés para mantener
el contacto abierto. Con mouse o teclado, mantené el jack pulsado.
La ruta de entrada de audio se configura
en el Rack. El panel usa los buses actuales del plugin y los parámetros
públicos para el CV. El cableado arbitrario entre jacks de distintos
plugins requeriría una interfaz de CV en el grafo del host.

### Mapas de controladores

Los mapas `.rfmap` usan el ID del plugin y el ID estable de cada
parámetro, como en RF-5 y RF-106. Los enlaces de sesión tienen prioridad
sobre el mapa del controlador, y el mapa tiene prioridad sobre los
valores automáticos que RackForge obtiene de un `.rfcontroller`.

El paquete completo incluye `metadata/control-layout.json`. El archivo
asigna funciones a posiciones genéricas y RackForge genera el mapa
de fábrica con las posiciones que publica cada controlador. El host
puede aprovechar filas extra y la capa **Fn** cuando se configura un
modificador. Las asignaciones de usuario conservan su prioridad.

| Posiciones | En orden |
| --- | --- |
| Fila principal, 1–8 | Loudness Attack, Decay, Sustain, Contour Amount, Cutoff, Emphasis, Glide Time, Mod Mix |
| Segunda fila, 1–8 | Nivel de OSC1, OSC2, OSC3, Noise, Filter Attack, Decay, Sustain, External Level |
| Tercera fila, 1–8 | Tune, frecuencia de OSC2 y OSC3, Volume, Phones Vol, Oscillator CV, Filter CV, Loudness CV |
| Banco de switches 1, 1–8 | OSC1, OSC2, OSC3, Noise, External, Glide, Decay, Filter Mod |
| Banco de switches 2, 1–8 | Osc Mod, OSC3 Control, Track ⅓, Track ⅔, White/Pink, cable LO → EXT, S‑Trigger mientras se mantiene pulsado, selector de rango OSC3 |
| Banco de switches 3, 1–6 | Forma de onda de OSC1, OSC2 y OSC3, salida de monitor, contactos momentáneos de Glide y Decay |
| Pares de avance y retroceso | Rango de OSC1 y rango de OSC2 |

En el **KeyLab Essential mk3**, las dos primeras filas van a los
faders y los encoders del 1 al 8, y los dos primeros bancos de
switches a los pads A y B. Un pad asignado acciona el mando con su
nota MIDI consumida por RackForge. Los novenos controles siguen
gobernando el nivel y el panorama del Rack. Pitch Bend y CC1
siguen llegando a las ruedas de RF-D.

Como respaldo, el esquema declara estos roles del Control Profile v1
para los controladores o las configuraciones que usan enlaces semánticos.

| Rol | Mando de RF-D |
| --- | --- |
| `synth.oscillator.noise.level` | Noise Level |
| `synth.filter.cutoff` | Cutoff |
| `synth.filter.resonance` | Emphasis |
| `synth.filter.envelope.amount` | Contour Amount |
| `synth.envelope.amp.attack` | Loudness Attack |
| `synth.envelope.amp.decay` | Loudness Decay |
| `synth.envelope.amp.sustain` | Loudness Sustain |
| `performance.modulation` | Rueda Mod |
| `performance.expression` | Loudness CV |

Los tiempos en milisegundos usan recorrido logarítmico en el panel
y los mapas. **Decay** de la mano izquierda conmuta la caída final,
cuyo tiempo toma del mismo knob Decay de cada contorno. Todos los
mandos editables también admiten asignación manual. El medidor de
sobrecarga indica el estado del preamplificador.

La comprobación de integración compiló los 54 mandos editables
como destinos de un mapa y utilizó el perfil del KeyLab Essential
mk3 para verificar los valores automáticos. También verificó la
prioridad de sesión, mapa y perfil, y la escritura en WASM de
selectores, CV, pedales y realimentación.
RackForge generó mapas a partir del layout para 61 perfiles de
controlador de su catálogo. El ensayo verificó la cobertura del
KeyLab Essential mk3, los mapas de Launchkey Mini mk4 y nanoKONTROL2,
la escritura de pad en WASM y la incorporación del nuevo mapa de
fábrica con asignaciones existentes.

El cable de realimentación tiene dos extremos anclados y una curva
Bézier SVG. La holgura aumenta con la separación hasta un límite.
Un resorte amortiguado desplaza el centro de la curva al arrastrar
y al encastrar la segunda punta. El brillo sigue la normal local de
la curva. El terminal suelto gira con la tangente. Al enchufarlo,
queda visible su cara posterior circular, centrada en el jack,
y el cable cae desde el centro de esa cara.
La animación usa `requestAnimationFrame`
y se detiene al asentarse. Con movimiento reducido, la curva alcanza
su posición de reposo de inmediato. El gesto envía el parámetro
`output_feedback` por la misma interfaz que el resto del panel.
[Gestos de patch en VCV Rack](https://vcvrack.com/manual/GettingStarted) ·
[Modelo de resorte amortiguado, MIT](https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/pages/unit-ii-second-order-constant-coefficient-linear-equations/damped-harmonic-oscillators/).

### Rueda y entradas de modulación

En el Model D vintage, **Modulation Mix** mezcla OSC3 y ruido. La rueda
regula la intensidad de esa mezcla. **Oscillator Modulation** y
**Filter Modulation** habilitan los destinos. J1 y J2 inyectan sus
voltajes directamente en los controles de afinación y cutoff, con
independencia de la rueda. En RF-D, CC1 mueve la rueda y MIDI Learn puede
enviar el mismo CC a un parámetro CV mediante un enlace de RackForge.
[Manual de operación, pp. PDF 7 y 11](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=7) ·
[Fig. 9-17 del manual de servicio](https://manuals.fdiskc.com/tree/Moog/Moog%20Minimoog%20Service%20Manual.pdf#page=75) ·
[Modelo de modulación](RUIDO_Y_MODULACION_TOCABLES.md).

El **Mod. Src.** de la reedición recibe una fuente de modulación externa
en la rama normalizada del ruido. Las salidas **Pitch**, **Gate**,
**Velocity** y **After Pressure** también aparecen en su panel ampliado.
Esas conexiones pertenecen a la reedición y quedan fuera del perfil
vintage de RF-D.
[Manual de Moog, sección Top Patch Panel, pp. impresas 34–37](https://cdn.inmusicbrands.com/Moog/Model%20D/Minimoog_Model_D_Manual.pdf).

### Expresión del teclado

**Connections → Keyboard Expression** ofrece dos rutas opcionales que se
guardan con el programa. El ejemplo *Enhancing a Keyboard Performance*
del manual de la reedición (p. 40 impresa) conecta Velocity a Loudness y
After Pressure a Filter. RF-D usa esos destinos mediante MIDI y los
[nodos de CV ya modelados](ENTRADAS_CONTROL_TOCABLES.md).
Los dos faders usan un cursor metálico sobre una ranura oscura. Admiten
arrastre, ajuste por teclado y asignación MIDI desde el panel.

- **Velocity → Loudness** ajusta entre 0 y 100 % cuánto puede reducirse el
  voltaje de Loudness CV. Para una profundidad fraccional `d` y una
  velocidad MIDI `v` de 1 a 127, el segundo VCA recibe
  `V_loudness × (1 − d × (1 − v/127))`. La velocidad máxima conserva el
  nivel del panel. La voz retiene la última velocidad en la cola.
- **After Pressure → Filter** suma `V_depth × presión/127` al CV de corte,
  hasta el límite de +2 V del modelo. La profundidad va de 0 a 2 V.
  Se usa el mayor valor entre la presión de canal y la de la tecla.
  La presión se libera con la tecla, incluso bajo sustain. En Mono sigue
  la nota de prioridad baja. En Poly, el canal y la tecla se aplican por
  voz. Reset Controllers limpia ambas fuentes de presión del canal.

Ambas rutas reutilizan el suavizado de los CV de hasta 64 frames a 48 kHz.
Las profundidades y la conversión lineal de MIDI a voltios son decisiones
de RF-D. El manual describe el ruteo y el trim, y queda por medir su
respuesta en una unidad física. **Glide Lead** y **Brass Section**
demuestran esta extensión. El ajuste de fábrica **Model D Classic**
arranca en Mono con ambas profundidades en cero.
[Manual de Moog, p. 40](https://cdn.inmusicbrands.com/Moog/Model%20D/Minimoog_Model_D_Manual.pdf).

La prueba con MIDI mide el cambio de nivel por velocidad, el filtro en
respuesta a presión de canal y de tecla, y el aislamiento de voces.
RackForge reproduce el mismo audio que WASM directo con bloques de
128, 480 y 4096 frames. Los dos pases offline de RackForge a 128 frames
tuvieron picos de 0,542 y 0,441 ms, con cero plazos perdidos.
[Resultados](../evidence/rf_d_voice_development10.json).

### Pedales Glide y Decay

La Fig. 9-12 de SVC-204D muestra J1402 y J1401 en el controlador
izquierdo. El addendum 70-019 especifica los contactos normalmente
cerrados y los pedales de resistencia variable de 10 MΩ (Glide)
y 2,5 MΩ (Decay). El switch de panel en ON tiene prioridad. Con el
switch en OFF, la apertura del contacto activa el tiempo del panel.
La resistencia de 0 MΩ conserva el comportamiento del contacto cerrado.
[Manual de operación, p. PDF 17](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=17) ·
[Esquema de controlador izquierdo, p. PDF 70](https://manuals.fdiskc.com/tree/Moog/Moog%20Minimoog%20Service%20Manual.pdf#page=70).

- **Glide.** El jack puentea el potenciómetro de tiempo R2 de 5 MΩ
  entre la salida y el retorno de Glide. Al agregar una resistencia
  al jack, las dos ramas quedan en paralelo. RF-D conserva el tiempo
  calibrado de su reducción, resta su piso de 1 ms, convierte el
  tramo variable usando C6 = 1 µF y aplica el paralelo a ese tramo.
  Para resistencia en MΩ, su equivalente en tiempo al 1 % es
  `1000 × ln(100) × R` ms.
- **Decay.** El jack controla la rama de descarga común de C2 y C5
  hacia Q12. Con el contacto abierto, cada contorno usa el tiempo
  de su propio knob Decay. En la reducción, el camino extra se
  calibra con la descarga rápida de 5 ms ya existente. Se infiere
  su conductancia como la diferencia entre la tasa rápida y la
  normal de cada contorno, se agrega la resistencia del pedal en
  serie a ese camino equivalente y se suman las tasas de ambas
  ramas. Los capacitores nominales son de 10 µF. El cálculo se usa
  durante el release y conserva los tiempos con tecla sostenida.

Es una reducción RC de las dos tomas. Quedan abiertos el taper exacto
del pedal físico y el reparto de corriente de las dos ramas con sus
diodos y Q12 en conducción conjunta.
[SVC-204D, funcionamiento y esquemas pp. PDF 13, 65, 70 y 75](https://manuals.fdiskc.com/tree/Moog/Moog%20Minimoog%20Service%20Manual.pdf#page=13).

La prueba de desarrollo compara por bits las ruedas MIDI y la
automatización, además de comprobar el release de ambos contornos
y el efecto de soltar Glide durante el portamento. Los dos pases
offline de RackForge a 128 frames tuvieron picos de 0,232 y 0,247 ms,
con cero plazos perdidos.
[Resultados](../evidence/rf_d_voice_development09.json).

## Programs

La cabecera reúne la marca Rackforge Instruments, el modelo RF-D y
los controles de programas. En **PLAY**, el selector nativo de RackForge
muestra los bancos de fábrica **Mono** y **Poly** y el banco **User**.
**Save as Program** abre una ventana para ingresar el nombre. **Save**
guarda los ajustes actuales y **Cancel** cierra la ventana.
**Export .rfd** descarga el sonido del panel. Para incorporar
un archivo al banco **User**, abrir **CONFIG → Import .rfd**. Tras guardar
o importar, RF-D selecciona el programa nuevo. La biblioteca
de usuario admite 64 programas y RackForge gestiona su almacenamiento.
El guardado y la importación están disponibles en la instancia principal.

`.rfd` es JSON UTF-8 con el identificador `rackforge.rf-d.program` en
`format`, `version: 1`, `name` y un objeto `parameters` con los 45
ajustes guardables por identificador público estable. Los valores usan
las unidades del motor. Los parámetros booleanos se expresan como 0 o 1 y los
selectores como sus códigos numéricos. La importación verifica los rangos
antes de abrir el borrador. Los dos ajustes de expresión toman el valor
cero cuando se abre un programa anterior que se guardó sin ellos.
Los programas de usuario conservan los mandos de síntesis y salida,
el lazo LO → External y las profundidades de expresión. Los valores en
vivo de los jacks CV, S-Trigger, el medidor,
A-440, las ruedas, los pedales, los enlaces MIDI y el selector
[Voices](POLIFONIA_RF_D.md) pertenecen a la interpretación o a la sesión.
Los programas de fábrica eligen el modo de voz según el banco.

[Manual de operación y addendum 70-019](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf#page=17) ·
[SVC-204D, Fig. 9-12 y 9-17, pp. PDF 70 y 75](FUENTES.md) ·
[Entradas CV y S-Trigger](ENTRADAS_CONTROL_TOCABLES.md) ·
[Salida HI/LO y Phones](SALIDA_TOCABLE.md) ·
[Cable LO → External](REALIMENTACION_TOCABLE.md).
