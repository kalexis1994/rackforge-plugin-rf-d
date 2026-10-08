# Descriptor local del reset: modos y alcance numérico

2026-10-08. Después del rechazo SDIRK01. Tres historias congeladas: primer piso Euler/Q6, segundo piso Euler/XIC3.7 y último estado del prefijo SDIRK. No cambiar estados, parámetros, métodos o gates. Es análisis lineal local, no prueba de estabilidad global, frecuencia o causa física de toda conmutación.

Evaluar F y G=∂F/∂x con leyes/incidencias Decimal100. En x=historia, obtener M=∂Q/∂x desde (J_Euler−G)*dt, restando en Decimal antes de convertir a float. Incluye todas las cargas y cuatro flujos inductivos; restricciones algebraicas conservadas. M tiene filas A·s/V y V·s/A según su incidencia. Las ecuaciones linealizadas son M δx' + G δx=0. El modo satisface (G+λM)v=0.

Sin instalar otro runtime: numpy solve/eig de T=(G+M/dt)^−1(M/dt), con dt=1 fs/1 ps/1 ns. Equilibrar filas del sistema y columnas [1 V,1 mA]; convertir μ de T a λ=(1−1/μ)/dt. Descartar μ≈0 (<1e-10) en esa ruta, sin llamarlos polos infinitos certificados. Sólo considerar candidatos cuyo residual por filas del lápiz original, reconstruido con aritmética Decimal100 compleja separada, sea ≤1e-8 relativo. No es un enclosure o prueba de multiplicidad; condición, redondeo y candidatos ausentes deben declararse.

Buscar coincidencias entre los tres shifts por distancia relativa compleja ≤1e-3. Registrar los modos rápidos estables e inestables, vectores completos, filas/nodos dominantes y residual. Una coincidencia local no demuestra causalidad física ni permite eliminar una dinámica. Estudiar también la relación nominal L3/RL3=100 pH/100 kΩ=1 fs, declarando que es una escala de la rama aislada del macromodelo, no un polo del circuito acoplado ni una bobina del instrumento.

Identidades de herramientas/fuentes/privados y inputs antes/después. Si un análisis falla, conservar y repetir los mismos arrays/funciones antes de reparar. No procesos SPICE, audio o cambios de producción. No ampliar campaña por este análisis.
