import cv2


def detect_objects(frame):
    """
    Detecta candidatos a objetos usando contornos.

    Retorna uma lista de objetos com:
    x, y, width, height, center_x, center_y, area
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Reduz pequenos detalhes e ruído
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detecta bordas
    edges = cv2.Canny(
        blurred,
        threshold1=50,
        threshold2=150
    )

    # Fecha pequenas interrupções nas bordas
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    edges = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    objects = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        area = w * h

        # Ignora coisas muito pequenas
        if area < 300:
            continue

        # Ignora regiões gigantes
        if area > frame.shape[0] * frame.shape[1] * 0.30:
            continue

        center_x = x + w / 2
        center_y = y + h / 2

        objects.append({
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "center_x": center_x,
            "center_y": center_y,
            "area": area
        })

    return objects, edges