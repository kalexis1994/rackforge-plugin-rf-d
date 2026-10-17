# Continuación DC del extremo alto

Native02 completa nueve OPs con semilla analítica y vuelve a fallar en
KEYBOARD=-.1 V/BUS=-.125 V; original y replay preservados antes de cambiar.
Para los tres puntos altos usar exclusivamente la raíz SPICE del mismo
BUS a -1.1 V como nodeset y recorrer DC VKEYBOARD de -1.1 a -.1 V, paso
.125 V. Conservar el último punto como raíz objetivo; registrar los nueve
puntos del sweep y comprobar el voltaje final y residual de las ecuaciones
originales. No importar raíz nativa, cambiar dispositivos, tolerancias,
forcing C1=0 o trims. Es continuación de Newton en DC, no transición
temporal ni prueba de unicidad. Los nueve OP previos conservan su método.
