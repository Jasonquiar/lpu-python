# lpu-python

Versión del curso *Backend con Python · EstudIA* de **Let's Play Ultimate (LPU)**: el núcleo backend para registrar partidos de Ultimate Frisbee. El planillero anota cada gol en el momento y capitanes y organizadores ven el marcador correcto.

> Todos los equipos y personas de este repositorio son **ficticios**.

## Ficha del proyecto

**Ámbito y quién usaría el servicio:** registro de partidos de Ultimate Frisbee. Lo usan el planillero (scorekeeper), que anota los goles, y los capitanes y organizadores, que consultan el marcador.

**Necesidad 1** (qué se registra, consulta o modifica): como planillero, necesito registrar cada gol en el momento en que ocurre, sin pasar después la planilla en papel a un Excel.

**Necesidad 2:** como capitán u organizador, necesito ver el marcador correcto y saber cuándo terminó el partido.

**Regla de negocio** (algo que el servicio nunca debe permitir o siempre debe cumplir): no se puede anotar un gol en un partido que ya terminó (un equipo llegó al máximo de goles, 15 por defecto), ni a un equipo que no está jugando ese partido.

| Caso | Entrada | Resultado esperado | Motivo |
|---|---|---|---|
| Aceptación | Partido 14-10, gol de "Equipo Rojo" | Queda 15-10 y el partido termina | El partido no había terminado y el equipo juega este partido |
| Rechazo por regla | Partido 15-10, otro gol | `GolRechazado` | El partido ya terminó |
| Rechazo por regla | Gol de "Equipo Verde" | `GolRechazado` | Ese equipo no juega este partido |
| Rechazo por dato inválido | Crear un partido "Equipo Rojo" vs "equipo rojo" | `ValueError` | Un equipo no puede jugar contra sí mismo |

**Qué dejo fuera por ahora:** torneo, categoría, jugadores, estadísticas (G, A, B, Callahan), tiempos, espíritu, W.O. y modo sin conexión. La lista completa está en el docstring de `src/modelo.py`.

## Cómo ejecutarlo

```bash
python3 src/modelo.py
```

## Estado

Distingue siempre qué está **ejecutado y comprobado**, qué está **simulado** y qué queda **pendiente**.

| Parte | Estado | Evidencia |
|---|---|---|
| Brief en el docstring de `src/modelo.py` | Escrito | Docstring de `src/modelo.py` |
| Modelo `Partido` con su regla (`registrar_gol`, `GolRechazado`) | Ejecutado y comprobado | `python3 src/modelo.py` (salida abajo) |
| Casos: 1 aceptado, 2 rechazados por regla, 1 por dato inválido | Ejecutado y comprobado | La salida coincide con lo esperado escrito en el código |
| El marcador no se puede asignar por fuera | Ejecutado y comprobado | `partido.marcador = (0, 0)` → `AttributeError` |
| Pruebas automáticas (pytest) | Pendiente | Encuentro 3 |

Salida de `python3 src/modelo.py`:

```text
Antes: Equipo Rojo 14 - 10 Equipo Azul (en juego)
ACEPTADO  Equipo Rojo -> Equipo Rojo 15 - 10 Equipo Azul (terminado)
RECHAZADO Equipo Azul -> El partido ya terminó: Equipo Rojo 15 - 10 Equipo Azul (terminado)
RECHAZADO Equipo Verde -> Equipo Verde no juega este partido (Equipo Rojo vs Equipo Azul)
DATO INVÁLIDO -> Un equipo no puede jugar contra sí mismo: Equipo Rojo
NO SE PUEDE -> property 'marcador' of 'Partido' object has no setter
Partido('Equipo Rojo' 15-10 'Equipo Azul', goles_maximos=15, terminado=True)
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
