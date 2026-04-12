from XboxController import XboxController
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import urllib.request
import os

controller = XboxController()

WEBCAM_PORT = 1


# ── Modèle ────────────────────────────────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

if not os.path.exists(MODEL_PATH):
    print("Téléchargement du modèle MediaPipe...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Modèle téléchargé.")

# ── Détecteur ─────────────────────────────────────────────────────────────────
base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.5,
)
detector = vision.HandLandmarker.create_from_options(options)

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]


# ─────────────────────────────────────────────────────────────────────────────
#  Fonctions principales
# ─────────────────────────────────────────────────────────────────────────────

def get_hand_center_px(landmarks, img_w: int, img_h: int) -> tuple[int, int]:
    """Retourne le centre de la main en pixels (x, y) dans l'image complète."""
    n = len(landmarks)
    cx = int(sum(lm.x for lm in landmarks) / n * img_w)
    cy = int(sum(lm.y for lm in landmarks) / n * img_h)
    return (cx, cy)


def get_normalized_position(
    cx: int, cy: int, img_w: int, img_h: int, side: str
) -> tuple[float, float]:
    """
    Retourne la position normalisée de la main dans SA moitié de l'image.

    La zone de chaque main est :
      - main gauche  (side="Left")  : x ∈ [0,       img_w/2]
      - main droite  (side="Right") : x ∈ [img_w/2, img_w  ]
    Dans les deux cas y ∈ [0, img_h].

    Returns:
        (nx, ny) avec nx, ny ∈ [-1.0, 1.0]
        (-1, -1) = coin haut-gauche de la zone
        ( 1,  1) = coin bas-droit de la zone
        ( 0,  0) = centre de la zone
    """
    half_w = img_w / 2

    if side == "Left":
        # zone x : [0, half_w]
        nx = (cx / half_w) * 2 - 1
    else:
        # zone x : [half_w, img_w]
        nx = ((cx - half_w) / half_w) * 2 - 1

    ny = (cy / img_h) * 2 - 1

    # Clamp dans [-1, 1] si la main dépasse sa zone
    nx = max(-1.0, min(1.0, round(nx, 3)))
    ny = max(-1.0, min(1.0, round(ny, 3)))
    return (nx, ny)


# ─────────────────────────────────────────────────────────────────────────────
#  Fonctions de dessin
# ─────────────────────────────────────────────────────────────────────────────

def draw_zones(frame, img_w, img_h):
    """Divise l'image en deux zones avec labels et grilles."""
    mid = img_w // 2

    # Fond teinté léger pour chaque zone
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0),   (mid, img_h),   (180, 100, 50),  -1)  # gauche – bleu
    cv2.rectangle(overlay, (mid, 0), (img_w, img_h), (50,  100, 180), -1)  # droite – rouge
    cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

    # Ligne de séparation
    cv2.line(frame, (mid, 0), (mid, img_h), (200, 200, 200), 2)

    # Croix de référence (centre de chaque zone)
    for zone_cx in (mid // 2, mid + mid // 2):
        cy_ref = img_h // 2
        cv2.line(frame, (zone_cx - 20, cy_ref), (zone_cx + 20, cy_ref), (100, 100, 100), 1)
        cv2.line(frame, (zone_cx, cy_ref - 20), (zone_cx, cy_ref + 20), (100, 100, 100), 1)

    # Labels de zone
    cv2.putText(frame, "GAUCHE", (mid // 2 - 45, img_h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 140, 80), 2)
    cv2.putText(frame, "DROITE", (mid + mid // 2 - 40, img_h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 140, 180), 2)


def draw_skeleton(frame, landmarks, img_w, img_h, color):
    pts = [(int(lm.x * img_w), int(lm.y * img_h)) for lm in landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2)
    for pt in pts:
        cv2.circle(frame, pt, 4, (255, 255, 255), -1)
        cv2.circle(frame, pt, 4, color, 1)


def draw_normalized_indicator(frame, cx, cy, nx, ny, color, img_w, img_h, side):
    """Affiche le point central et sa position normalisée."""
    # Croix + cercle
    size = 14
    cv2.line(frame, (cx - size, cy), (cx + size, cy), color, 2)
    cv2.line(frame, (cx, cy - size), (cx, cy + size), color, 2)
    cv2.circle(frame, (cx, cy), 9, color, -1)

    # Étiquette normalisée
    label = f"({nx:.2f}, {ny:.2f})"
    offset_x = 14 if (side == "Right" or cx < img_w - 160) else -175
    cv2.putText(frame, label, (cx + offset_x, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Mini-visu : carré (-1,1) avec point dedans
    sq_x = 10 if side == "Left" else img_w // 2 + 10
    sq_y = img_h - 110
    sq_size = 80
    # Carré de référence
    cv2.rectangle(frame, (sq_x, sq_y), (sq_x + sq_size, sq_y + sq_size), (80, 80, 80), 1)
    # Axes
    mid_sq = sq_x + sq_size // 2
    mid_sq_y = sq_y + sq_size // 2
    cv2.line(frame, (mid_sq, sq_y), (mid_sq, sq_y + sq_size), (60, 60, 60), 1)
    cv2.line(frame, (sq_x, mid_sq_y), (sq_x + sq_size, mid_sq_y), (60, 60, 60), 1)
    # Point dans le carré
    dot_x = int(sq_x + (nx + 1) / 2 * sq_size)
    dot_y = int(sq_y + (ny + 1) / 2 * sq_size)
    dot_x = max(sq_x, min(sq_x + sq_size, dot_x))
    dot_y = max(sq_y, min(sq_y + sq_size, dot_y))
    cv2.circle(frame, (dot_x, dot_y), 6, color, -1)
    cv2.putText(frame, label, (sq_x, sq_y - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Boucle principale
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {"Left": (200, 140, 50), "Right": (50, 140, 220)}  # BGR

cap = cv2.VideoCapture( WEBCAM_PORT )
if not cap.isOpened():
    raise RuntimeError("Impossible d'ouvrir la caméra.")

print("Appuyez sur 'q' pour quitter.")
timestamp_ms = 0

def invertYAxis( position: tuple[float, float]) -> tuple[float, float]:
    x, y = position
    return (x, -y)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    img_h, img_w = frame.shape[:2]

    draw_zones(frame, img_w, img_h)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    result = detector.detect_for_video(mp_image, timestamp_ms)
    timestamp_ms += 33

    info_lines = []

    # Positions par défaut : (0, 0) si la main n'est pas détectée
    positions: dict[str, tuple[float, float]] = {"Left": (0.0, 0.0), "Right": (0.0, 0.0)}

    if result.hand_landmarks:
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            # Après cv2.flip(frame, 1) les côtés sont inversés
            raw_side = handedness[0].display_name
            side = "Right" if raw_side == "Left" else "Left"
            color = COLORS.get(side, (255, 255, 255))

            draw_skeleton(frame, landmarks, img_w, img_h, color)

            cx, cy = get_hand_center_px(landmarks, img_w, img_h)
            nx, ny = get_normalized_position(cx, cy, img_w, img_h, side)
            # ny *= -1
            positions[side] = (nx, ny)

            draw_normalized_indicator(frame, cx, cy, nx, ny, color, img_w, img_h, side)

            info_lines.append(f"{side:5s} → ({nx:+.2f}, {ny:+.2f})")

    # Toujours afficher les deux positions (avec (0,0) si non détectée)
    print(f"Left={positions['Left']}  Right={positions['Right']}")
    controller.joystick.setLeftJoystick(*invertYAxis(positions["Left"]))
    controller.joystick.setRightJoystick(*invertYAxis(positions["Right"]))
    controller.apply()

    # Panneau info haut
    if not info_lines:
        info_lines = ["Placez chaque main dans sa zone"]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (img_w, 28 + len(info_lines) * 28), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    for i, line in enumerate(info_lines):
        cv2.putText(frame, line, (10, 22 + i * 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    cv2.imshow("Position normalisée par zone - OpenCV + MediaPipe", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()