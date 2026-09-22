"""
VisualStimulus — dado sensorial bruto que o sistema de visão
entrega ao cérebro. Não contém rótulos ("reward", "threat"),
apenas propriedades físicas observáveis.

O cérebro (SensoryEncoder + circuitos) é quem decide o que
fazer com cada estímulo.
"""

from dataclasses import dataclass, field


@dataclass
class VisualStimulus:
    """
    Representa um objeto detectado no campo visual.

    Todos os valores são normalizados [0, 1] salvo indicação.

    Atributos
    ---------
    x, y            : posição do centro no frame (0=esq/topo, 1=dir/baixo)
    apparent_size   : tamanho aparente — área_pixels / área_frame
                      proxy de proximidade (maior = mais perto ou maior)
    contrast        : compacidade do contorno (quão "sólido" é o objeto)
                      1.0 = círculo perfeito, 0.1 = forma muito espalhada
    velocity_x      : movimento horizontal entre frames (positivo = direita)
    velocity_y      : movimento vertical entre frames (positivo = baixo)
    track_id        : ID do tracker (None se não rastreado)
    age             : quantos frames este objeto é visível
    """

    x:             float
    y:             float
    apparent_size: float
    contrast:      float

    velocity_x:    float = 0.0
    velocity_y:    float = 0.0
    track_id:      int | None = None
    age:           int = 1


def items_to_visual_field(
    items: list[dict],
    frame_width: int,
    frame_height: int,
    tracked_objects: dict | None = None,
) -> list[VisualStimulus]:
    """
    Converte a lista de dicts do detect.py em VisualStimuli.

    Parâmetros
    ----------
    items           : saída de detect_items()
    frame_width     : largura do frame em pixels
    frame_height    : altura em pixels
    tracked_objects : dict {id: TrackedObject} do tracking.py (opcional)
                      se fornecido, adiciona velocidade e age

    Retorna
    -------
    Lista de VisualStimulus, um por item detectado.
    """
    frame_area = frame_width * frame_height
    stimuli = []

    for item in items:
        nx = item["center_x"] / frame_width
        ny = item["center_y"] / frame_height

        # Tamanho aparente: fração da área do frame
        apparent_size = min(item["area"] / frame_area, 1.0)

        # Contraste: compacidade do contorno
        # area_contorno / area_bbox — já calculado como "score" no detect
        # Mas usamos compact se disponível, senão inferimos do score
        contrast = min(item.get("score", 0.5), 1.0)

        vx, vy = 0.0, 0.0
        track_id = None
        age = 1

        # Enriquece com dados de tracking se disponível
        if tracked_objects:
            tid = item.get("track_id")
            if tid is not None and tid in tracked_objects:
                obj = tracked_objects[tid]
                vx  = obj.movement / frame_width   # normaliza pelo width
                vy  = 0.0                          # tracking.py só dá magnitude
                age = obj.age
                track_id = tid

        stimuli.append(VisualStimulus(
            x=nx,
            y=ny,
            apparent_size=apparent_size,
            contrast=contrast,
            velocity_x=vx,
            velocity_y=vy,
            track_id=track_id,
            age=age,
        ))

    return stimuli