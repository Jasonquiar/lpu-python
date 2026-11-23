"""MI BRIEF · Let's Play Ultimate (LPU) · Encuentro 2

Actor: el planillero (scorekeeper) del partido.

Operación: registrar cada gol en el momento en que ocurre (modificar el marcador)
y consultar el marcador y si el partido ya terminó.

Recursos: un Partido con equipo_a y equipo_b (texto, ej. "Equipo Rojo"), el marcador
de cada equipo y goles_maximos (15 por defecto). En LPU, goles_maximos lo define el
líder de torneo al crear el torneo; como Torneo todavía no existe en este modelo,
el valor llega al crear el Partido.

Regla: el marcador solo avanza por la vía válida (registrar_gol). No se registra un gol:
  - si el partido ya terminó (un equipo llegó a goles_maximos), ni
  - a un equipo que no juega este partido.
  Ambos casos → GolRechazado (regla de negocio).
  Datos inválidos → ValueError: nombre vacío, equipo_a igual a equipo_b, goles_maximos <= 0.
  Los nombres se comparan sin espacios al borde y sin distinguir mayúsculas.
  El marcador es de solo lectura y solo cambia por registrar_gol.
  goles_maximos no se puede cambiar después de crear el partido.

Exclusiones: torneo, categoría, jugadores, asistencias, bloqueos, Callahan, tiempos,
espíritu y W.O.

Primer flujo verificable: con el partido 14-10, registrar_gol("Equipo Rojo") → queda 15-10
y terminado es True. Un gol más → GolRechazado. Un gol de "Equipo Verde" → GolRechazado.

¿Clase o función? Clase. Hay un estado que cambia (el marcador) y una regla que lo
protege. Con una función y un diccionario, cualquiera podría modificar el marcador por
fuera; con la clase, el marcador es de solo lectura y solo avanza por registrar_gol.

Pendiente:
  - Tildes en los nombres ("Bogotá" vs "Bogota").
  - Torneo: el líder de torneo define goles_maximos para todos los partidos (otra entidad).
  - El planillero no puede jugar en el torneo donde planilla (otra entidad).
  - Ayudas de tiempo: inicio, pull de 75 s, tiempos fuera, medio tiempo (8 goles o 45 min)
    y límite de tiempo (85 min).
  - Goles por W.O.: 1 gol cada 3 min si el rival no llega (mínimo 5 jugadores en línea).
  - Estadísticas por jugador (G, A, B, Callahan), caídos y espíritu.
  - Modo sin conexión: guardar en el dispositivo y sincronizar después.
"""


class OperacionRechazada(Exception):
    """Rechazo de negocio: cambia el nombre por el de tu regla."""


class Recurso:  # cambia el nombre: Reserva, Pedido, Turno, Producto…
    def __init__(self, nombre, cantidad):
        self.nombre = nombre
        self.cantidad = cantidad  # pasa por el setter: la regla se aplica desde el inicio

    @property
    def cantidad(self):
        return self._cantidad

    @cantidad.setter
    def cantidad(self, valor):
        if valor < 0:  # REGLA: cámbiala por la tuya
            raise OperacionRechazada(f"Cantidad inválida: {valor}")
        self._cantidad = valor

    def operar(self, valor):  # cambia el nombre por tu operación
        if valor <= 0:
            raise ValueError(f"Dato inválido: {valor}")
        self.cantidad -= valor  # si rompe la regla, el setter lo rechaza
        return self.cantidad

    def __repr__(self):
        return f"Recurso({self.nombre!r}, cantidad={self.cantidad})"

    def __str__(self):
        return f"{self.nombre}: {self.cantidad}"


if __name__ == "__main__":
    recurso = Recurso("Ejemplo", 5)

    # Dos casos: uno que se acepta y uno que se rechaza. Escribe antes qué esperas.
    for valor in [3, 10]:
        try:
            print("ACEPTADO ", valor, "->", recurso.operar(valor))
        except OperacionRechazada as error:
            print("RECHAZADO", valor, "->", error)
    print(recurso)
