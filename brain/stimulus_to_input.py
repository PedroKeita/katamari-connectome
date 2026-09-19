def stimulus_to_inputs(stimuli):
    left = 0.0
    center = 0.0
    right = 0.0

    for stimulus in stimuli:
        x = stimulus.x
        intensity = stimulus.intensity

        # Esquerda
        if x < 0.5:
            left_strength = (0.5 - x) / 0.5
            left += intensity * left_strength

        # Direita
        if x > 0.5:
            right_strength = (x - 0.5) / 0.5
            right += intensity * right_strength

        # Centro
        center_distance = abs(x - 0.5)
        center_strength = max(0.0, 1.0 - center_distance / 0.5)
        center += intensity * center_strength

    # Evita valores exagerados
    left = min(left, 1.0)
    center = min(center, 1.0)
    right = min(right, 1.0)

    return left, center, right