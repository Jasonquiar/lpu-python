# lpu-python

Versión del curso *Backend con Python · EstudIA* de **Let's Play Ultimate (LPU)**: el núcleo backend para registrar partidos de Ultimate Frisbee. El planillero anota cada jugada en el momento, el sistema lleva el tiempo y le avisa, y capitanes y organizadores ven el marcador correcto.

> Todos los equipos y personas de este repositorio son **ficticios**.

## Ficha del proyecto

**Ámbito y quién usaría el servicio:** registro de partidos de Ultimate Frisbee. Lo usan el planillero (scorekeeper), que anota cada jugada con ayuda del control de tiempo, y los capitanes y organizadores, que consultan el marcador.

**Necesidad 1** (qué se registra, consulta o modifica): como planillero, necesito registrar cada gol en el momento en que ocurre, sin pasar después la planilla en papel a un Excel.

**Necesidad 2:** como capitán u organizador, necesito ver el marcador correcto y saber cuándo terminó el partido.

**Regla de negocio** (algo que el servicio nunca debe permitir o siempre debe cumplir): el marcador solo avanza por la vía válida. No se puede anotar un gol sin una jugada activa (falta el pull), a un equipo que no está jugando ese partido, ni en un partido que ya terminó. El partido termina **por goles** (un equipo llega al máximo que definió el líder de torneo, 15 por defecto) o **por tiempo** (se cumplió el tiempo, no hay jugada activa y no hay empate). Nunca termina empatado.

| Caso | Entrada | Resultado esperado | Motivo |
|---|---|---|---|
| Aceptación | Partido 14-10, pull y gol de "Equipo Rojo" | Queda 15-10, terminado por goles | El partido seguía abierto, había jugada activa y el equipo juega |
| Aceptación | 14-10, se cumple el tiempo con la jugada activa, gol de "Equipo Azul" | Queda 14-11, terminado por tiempo | Con la jugada activa, el partido sigue hasta el próximo gol |
| Aceptación | 10-10, se cumple el tiempo | Sigue en juego; el próximo gol lo cierra (11-10) | Un partido nunca termina empatado |
| Aceptación | Pull vencido (75 s), el ataque inicia desde el brick | Jugada activa | La defensa se pasó del tiempo de pull |
| Rechazo por regla | Gol sin pull | `GolRechazado` | No hay jugada activa |
| Rechazo por regla | Partido terminado, otro gol | `GolRechazado` | El partido ya terminó |
| Rechazo por regla | Gol de "Equipo Verde" | `GolRechazado` | Ese equipo no juega este partido |
| Rechazo por regla | Iniciar desde el brick antes de que venza el pull | `JugadaRechazada` | La defensa todavía tiene tiempo de pull |
| Rechazo por dato inválido | Crear un partido "Equipo Rojo" vs " equipo rojo " | `ValueError` | Un equipo no puede jugar contra sí mismo |

**Qué dejo fuera por ahora:** torneo, categoría, jugadores, estadísticas (G, A, B, Callahan), tiempos fuera, espíritu, partido no jugado, W.O. y modo sin conexión. La lista completa está en el docstring de `src/modelo.py`.

## Cómo ejecutarlo

```bash
python3 src/modelo.py
```

## Estado

Distingue siempre qué está **ejecutado y comprobado**, qué está **simulado** y qué queda **pendiente**.

| Parte | Estado | Evidencia |
|---|---|---|
| Brief en el docstring de `src/modelo.py` | Escrito | Docstring de `src/modelo.py` |
| `Reglamento` (lo que define el líder de torneo) | Ejecutado y comprobado | Escenario 2 de la demo |
| `Partido`: jugadas (pull, brick, gol), fin por goles y por tiempo | Ejecutado y comprobado | Escenarios 1, 3, 4, 5 y 6 |
| `ControlDeTiempo`: avisos de pull, medio tiempo, 5 minutos y tiempo cumplido | Ejecutado y comprobado con un reloj de mentira | Escenarios 3 a 6 |
| El estado no se puede asignar por fuera | Ejecutado y comprobado | `partido.marcador = (0, 0)` → `AttributeError` |
| Reloj real corriendo cada segundo | Pendiente | Llega con la app o la API |
| Pruebas automáticas (pytest) | Pendiente | Encuentro 3 |

La salida real coincide línea por línea con lo esperado, escrito antes de ejecutar en los comentarios `# Espero:` del código.

Salida de `python3 src/modelo.py`:

```text
== 1 · Jugadas y fin por goles
  Inicio: Equipo Rojo 0 - 0 Equipo Azul (en juego) | ataca: Equipo Rojo | defiende: Equipo Azul
  RECHAZADO gol sin pull -> GolRechazado: No hay jugada activa: falta el pull de Equipo Azul
  ACEPTADO  gol de la defensa (Azul) -> Equipo Rojo 0 - 1 Equipo Azul (en juego)
  Ahora ataca: Equipo Azul | defiende: Equipo Rojo
  ACEPTADO  gol de Rojo con 14-10 -> Equipo Rojo 15 - 10 Equipo Azul (terminado por goles)
  RECHAZADO otro pull -> JugadaRechazada: El partido ya terminó: Equipo Rojo 15 - 10 Equipo Azul (terminado por goles)
  RECHAZADO gol de Equipo Verde -> GolRechazado: Equipo Verde no juega este partido (Equipo Rojo vs Equipo Azul)
  NO SE PUEDE -> property 'marcador' of 'Partido' object has no setter
== 2 · Datos inválidos
  DATO INVÁLIDO mismo equipo -> Un equipo no puede jugar contra sí mismo: Equipo Rojo
  DATO INVÁLIDO ataca un equipo ajeno -> El equipo que ataca primero no juega este partido: Equipo Verde
  DATO INVÁLIDO pull de 10 s -> tiempo_pull_segundos debe ser mayor que 15 (el aviso de pull se da 15 s antes)
== 3 · Tiempo de pull y brick (pull de 75 s)
  [00:00] (sin avisos)
  [01:00] AVISO: Se acaba el tiempo de pull: avisa a Equipo Rojo (defensa)
  [01:15] AVISO: Pull vencido: avisa a Equipo Azul (ataque) que puede iniciar desde el brick
  ACEPTADO  iniciar desde el brick -> Equipo Rojo 0 - 0 Equipo Azul (en juego)
  [01:45] (sin avisos)
  RECHAZADO brick sin pull vencido -> JugadaRechazada: No se puede iniciar desde el brick: Equipo Rojo todavía tiene tiempo de pull
== 4 · Fin por tiempo con la jugada activa (85 min)
  [40:00] AVISO: Medio tiempo: Equipo Rojo 8 - 6 Equipo Azul (en juego)
  [80:00] AVISO: Faltan 5 minutos: se acerca la última jugada
  [85:00] AVISO: Tiempo cumplido con la jugada activa: el partido termina con el próximo gol
  ACEPTADO  gol de Azul en la última jugada -> Equipo Rojo 14 - 11 Equipo Azul (terminado por tiempo)
  RECHAZADO gol de Rojo después del final -> GolRechazado: El partido ya terminó: Equipo Rojo 14 - 11 Equipo Azul (terminado por tiempo)
== 5 · Fin por tiempo con empate: se juega una jugada más
  [85:00] AVISO: Medio tiempo: Equipo Rojo 10 - 10 Equipo Azul (en juego)
  [85:00] AVISO: Faltan 5 minutos: se acerca la última jugada
  [85:00] AVISO: Tiempo cumplido con empate: se juega una jugada más
  ACEPTADO  gol de Rojo en la jugada extra -> Equipo Rojo 11 - 10 Equipo Azul (terminado por tiempo)
== 6 · Fin por tiempo sin jugada activa y sin empate
  [85:00] AVISO: Medio tiempo: Equipo Rojo 12 - 9 Equipo Azul (en juego)
  [85:00] AVISO: Faltan 5 minutos: se acerca la última jugada
  [85:00] AVISO: Tiempo cumplido: el partido terminó. Equipo Rojo 12 - 9 Equipo Azul (terminado por tiempo)
  Partido('Equipo Rojo' 12-9 'Equipo Azul', ataca='Equipo Azul', terminado='por tiempo')
```

## Bitácora de decisiones

| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-11-23 | La entidad es `Partido`, no `Torneo` | Es el corazón del sistema: lo que hace el planillero en la cancha |
| 2026-11-23 | `Partido` es una clase | Hay un estado que cambia (el marcador) y una regla que lo protege |
| 2026-11-23 | `goles_maximos` llega al crear el `Partido` y no cambia | En LPU lo define el líder de torneo al crear el torneo; `Torneo` queda pendiente |
| 2026-11-23 | La regla vive en `registrar_gol`, no en un setter | Un gol es un evento que suma 1, no un valor que se asigna |
| 2026-11-23 | El marcador es de solo lectura y todo partido empieza 0-0 | Si hubiera un marcador inicial o un setter, habría otra puerta para saltarse la regla |
| 2026-11-23 | `terminado` se calcula a partir del marcador, no se guarda | Así nunca puede quedar "15-10 pero sin terminar" |
| 2026-11-23 | Primero se valida el dato (`ValueError`) y después la regla (`GolRechazado`) | Si el dato no tiene sentido, no vale la pena revisar la regla |
| 2026-11-23 | Se guarda el nombre original y se compara el normalizado | Se muestra bien ("Equipo Rojo") y no falla por mayúsculas ni espacios |
| 2026-11-23 | El sistema lleva el tiempo y avisa al planillero | Así el planillero está pendiente de las jugadas y no del reloj |
| 2026-11-23 | Las reglas (`Partido`) y el reloj (`ControlDeTiempo`) van separados; el control *tiene* un partido | El partido no depende del reloj real: se prueba en milisegundos con un reloj de mentira |
| 2026-11-23 | Los valores del reglamento van en `Reglamento`, que el partido *tiene* | Los define el líder de torneo al crear el torneo; composición, sin herencia |
| 2026-11-23 | Quien anota sigue atacando; a quien le anotaron pasa a defender | Regla de los torneos de LPU |
| 2026-11-23 | Un partido nunca termina empatado | Con el tiempo cumplido y empate, se juega una jugada más |
| 2026-11-23 | Dos excepciones: `GolRechazado` y `JugadaRechazada` | Separan los rechazos de goles de los de pull, brick y tiempo |
| 2026-11-23 | Todo queda en un solo archivo, `src/modelo.py` | Un archivo que define el modelo completo, como pide el Encuentro 2 |
