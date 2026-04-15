"""
xbox_controller.py
==================
Classe XboxController avec sous-classes Buttons et Joystick,
utilisant vgamepad (ViGEmBus) pour créer une manette virtuelle
reconnue par la Driver Station FRC.

Dépendances :
    pip install vgamepad

Exemple d'utilisation :
    from xbox_controller import XboxController

    ctrl = XboxController()

    ctrl.buttons.setButtonState("A", True)
    ctrl.joystick.setLeftJoystick(0.5, -0.3)
    ctrl.joystick.setTriggerAxis("left", 0.8)
    ctrl.apply()   # Envoie l'état au driver virtuel

    print(ctrl.buttons.getButtonState("A"))        # True
    print(ctrl.joystick.getLeftJoystick())          # (0.5, -0.3)
    print(ctrl.joystick.getTriggerAxis("left"))     # 0.8
"""

from __future__ import annotations
from typing import Tuple
import vgamepad as vg


# ──────────────────────────────────────────────────────────────────────────────
# Sous-classe : Buttons
# ──────────────────────────────────────────────────────────────────────────────

class Buttons:
    """
    Gère l'état de tous les boutons d'une manette Xbox.

    Boutons disponibles :
        "A", "B", "X", "Y"
        "LB", "RB"
        "START", "BACK"
        "LS"  (clic joystick gauche)
        "RS"  (clic joystick droit)
        "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"

    Exemple :
        ctrl.buttons.setButtonState("A", True)
        pressed = ctrl.buttons.getButtonState("A")   # True
        ctrl.buttons.toggleButtonState("LB")
        all_states = ctrl.buttons.getAllStates()
    """

    # Noms valides (normalisés en majuscules)
    VALID_BUTTONS = {
        "A", "B", "X", "Y",
        "LB", "RB",
        "START", "BACK",
        "LS", "RS",
        "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
    }

    def __init__(self):
        # État interne : dict bouton → bool
        self._state: dict[str, bool] = {btn: False for btn in self.VALID_BUTTONS}

    # ── Setters ───────────────────────────────────────────────────────────────

    def setButtonState(self, button: str, pressed: bool) -> None:
        """
        Définit l'état d'un bouton.

        Args:
            button  : Nom du bouton (ex: "A", "LB", "DPAD_UP"). Insensible à la casse.
            pressed : True = appuyé, False = relâché.

        Raises:
            ValueError : Si le nom du bouton est invalide.
        """
        key = self._validate(button)
        self._state[key] = bool(pressed)

    def setAllButtons(self, pressed: bool) -> None:
        """Définit tous les boutons au même état (utile pour reset)."""
        for key in self._state:
            self._state[key] = bool(pressed)

    def toggleButtonState(self, button: str) -> bool:
        """
        Inverse l'état d'un bouton.

        Returns:
            Le nouvel état après toggle.
        """
        key = self._validate(button)
        self._state[key] = not self._state[key]
        return self._state[key]

    # ── Getters ───────────────────────────────────────────────────────────────

    def getButtonState(self, button: str, default: bool = False) -> bool:
        """
        Retourne l'état d'un bouton.

        Args:
            button  : Nom du bouton.
            default : Valeur retournée si le bouton est inconnu (défaut: False).

        Returns:
            True si appuyé, False sinon.
        """
        try:
            key = self._validate(button)
        except ValueError:
            return default
        return self._state.get(key, default)

    def getAllStates(self) -> dict[str, bool]:
        """Retourne une copie du dictionnaire complet {bouton: état}."""
        return dict(self._state)

    def getPressedButtons(self) -> list[str]:
        """Retourne la liste des boutons actuellement appuyés."""
        return [btn for btn, pressed in self._state.items() if pressed]

    # ── Interne ───────────────────────────────────────────────────────────────

    def _validate(self, button: str) -> str:
        """Normalise et valide un nom de bouton."""
        key = button.upper()
        if key not in self.VALID_BUTTONS:
            raise ValueError(
                f"Bouton invalide : '{button}'. "
                f"Valeurs acceptées : {sorted(self.VALID_BUTTONS)}"
            )
        return key

    def __repr__(self) -> str:
        pressed = self.getPressedButtons()
        return f"Buttons(pressed={pressed})"


# ──────────────────────────────────────────────────────────────────────────────
# Sous-classe : Joystick
# ──────────────────────────────────────────────────────────────────────────────

class Joystick:
    """
    Gère les axes analogiques de la manette Xbox :
      - Joystick gauche  (X, Y)   → [-1.0, 1.0]
      - Joystick droit   (X, Y)   → [-1.0, 1.0]
      - Gâchette gauche  (LT)     → [ 0.0, 1.0]
      - Gâchette droite  (RT)     → [ 0.0, 1.0]

    Convention des axes :
        X positif = droite
        Y positif = haut  (vgamepad inverse automatiquement l'axe Y)

    Exemple :
        ctrl.joystick.setLeftJoystick(0.5, -1.0)
        ctrl.joystick.setRightJoystick(0.0, 0.0)
        ctrl.joystick.setTriggerAxis("left",  0.8)
        ctrl.joystick.setTriggerAxis("right", 0.0)

        x, y = ctrl.joystick.getLeftJoystick()
        lt   = ctrl.joystick.getTriggerAxis("left")
    """

    def __init__(self):
        self._left_x:  float = 0.0   # Joystick gauche X
        self._left_y:  float = 0.0   # Joystick gauche Y
        self._right_x: float = 0.0   # Joystick droit X
        self._right_y: float = 0.0   # Joystick droit Y
        self._lt:      float = 0.0   # Gâchette gauche [0, 1]
        self._rt:      float = 0.0   # Gâchette droite [0, 1]

    # ── Setters ───────────────────────────────────────────────────────────────

    def setLeftJoystick(self, x: float, y: float) -> None:
        """
        Définit la position du joystick gauche.

        Args:
            x : Axe horizontal. -1.0 = gauche, 1.0 = droite.
            y : Axe vertical.   -1.0 = bas,    1.0 = haut.
        """
        self._left_x = self._clamp(x)
        self._left_y = self._clamp(y)

    def setRightJoystick(self, x: float, y: float) -> None:
        """
        Définit la position du joystick droit.

        Args:
            x : Axe horizontal. -1.0 = gauche, 1.0 = droite.
            y : Axe vertical.   -1.0 = bas,    1.0 = haut.
        """
        self._right_x = self._clamp(x)
        self._right_y = self._clamp(y)

    def setTriggerAxis(self, side: str, value: float) -> None:
        """
        Définit la valeur d'une gâchette.

        Args:
            side  : "left" (LT) ou "right" (RT). Insensible à la casse.
            value : Intensité entre 0.0 (relâchée) et 1.0 (enfoncée à fond).

        Raises:
            ValueError : Si side n'est pas "left" ou "right".
        """
        s = side.lower()
        val = self._clamp_trigger(value)
        if s == "left":
            self._lt = val
        elif s == "right":
            self._rt = val
        else:
            raise ValueError(f"Side invalide : '{side}'. Utilisez 'left' ou 'right'.")

    def resetAll(self) -> None:
        """Remet tous les axes à zéro."""
        self._left_x = self._left_y = 0.0
        self._right_x = self._right_y = 0.0
        self._lt = self._rt = 0.0

    # ── Getters ───────────────────────────────────────────────────────────────

    def getLeftJoystick(self, default: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """
        Retourne la position du joystick gauche.

        Args:
            default : Valeur retournée si non initialisé (défaut: (0.0, 0.0)).

        Returns:
            Tuple (x, y).
        """
        return (self._left_x, self._left_y)

    def getRightJoystick(self, default: Tuple[float, float] = (0.0, 0.0)) -> Tuple[float, float]:
        """
        Retourne la position du joystick droit.

        Returns:
            Tuple (x, y).
        """
        return (self._right_x, self._right_y)

    def getTriggerAxis(self, side: str, default: float = 0.0) -> float:
        """
        Retourne la valeur d'une gâchette.

        Args:
            side    : "left" ou "right".
            default : Valeur si side est invalide (défaut: 0.0).

        Returns:
            Float entre 0.0 et 1.0.
        """
        s = side.lower()
        if s == "left":
            return self._lt
        elif s == "right":
            return self._rt
        return default

    def getAllAxes(self) -> dict[str, float]:
        """
        Retourne tous les axes sous forme de dictionnaire.

        Returns:
            {
                "left_x": float, "left_y": float,
                "right_x": float, "right_y": float,
                "lt": float, "rt": float
            }
        """
        return {
            "left_x":  self._left_x,
            "left_y":  self._left_y,
            "right_x": self._right_x,
            "right_y": self._right_y,
            "lt":      self._lt,
            "rt":      self._rt,
        }

    # ── Interne ───────────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float) -> float:
        """Limite une valeur d'axe à [-1.0, 1.0]."""
        return max(-1.0, min(1.0, float(value)))

    @staticmethod
    def _clamp_trigger(value: float) -> float:
        """Limite une valeur de gâchette à [0.0, 1.0]."""
        return max(0.0, min(1.0, float(value)))

    def __repr__(self) -> str:
        return (
            f"Joystick("
            f"left=({self._left_x:.2f}, {self._left_y:.2f}), "
            f"right=({self._right_x:.2f}, {self._right_y:.2f}), "
            f"lt={self._lt:.2f}, rt={self._rt:.2f})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Classe principale : XboxController
# ──────────────────────────────────────────────────────────────────────────────

class XboxController:
    """
    Manette Xbox virtuelle pour la Driver Station FRC.
    Utilise vgamepad + ViGEmBus pour créer un contrôleur XInput reconnu
    nativement par Windows et la Driver Station.

    Sous-classes accessibles :
        controller.buttons  → instance de Buttons
        controller.joystick → instance de Joystick

    Workflow typique :
        ctrl = XboxController()

        # Modifier l'état
        ctrl.buttons.setButtonState("A", True)
        ctrl.joystick.setLeftJoystick(0.5, -0.3)
        ctrl.joystick.setTriggerAxis("right", 1.0)

        # Envoyer l'état à vgamepad (obligatoire pour que la DS le voie)
        ctrl.apply()

        # Lire l'état courant
        print(ctrl.buttons.getButtonState("A"))
        print(ctrl.joystick.getLeftJoystick())

        # Tout réinitialiser
        ctrl.reset()
        ctrl.apply()

    Raises:
        ImportError : Si vgamepad n'est pas installé.
        RuntimeError : Si ViGEmBus n'est pas installé sur Windows.
    """

    # Correspondance nom bouton → constante vgamepad
    _BUTTON_MAP: dict[str, str] = {
        "A":          "XUSB_GAMEPAD_A",
        "B":          "XUSB_GAMEPAD_B",
        "X":          "XUSB_GAMEPAD_X",
        "Y":          "XUSB_GAMEPAD_Y",
        "LB":         "XUSB_GAMEPAD_LEFT_SHOULDER",
        "RB":         "XUSB_GAMEPAD_RIGHT_SHOULDER",
        "START":      "XUSB_GAMEPAD_START",
        "BACK":       "XUSB_GAMEPAD_BACK",
        "LS":         "XUSB_GAMEPAD_LEFT_THUMB",
        "RS":         "XUSB_GAMEPAD_RIGHT_THUMB",
        "DPAD_UP":    "XUSB_GAMEPAD_DPAD_UP",
        "DPAD_DOWN":  "XUSB_GAMEPAD_DPAD_DOWN",
        "DPAD_LEFT":  "XUSB_GAMEPAD_DPAD_LEFT",
        "DPAD_RIGHT": "XUSB_GAMEPAD_DPAD_RIGHT",
    }

    def __init__(self):
        try:
            self._vg = vg
            self._gamepad = vg.VX360Gamepad()
        except ImportError:
            raise ImportError(
                "vgamepad n'est pas installé.\n"
                "Installez-le avec : pip install vgamepad\n"
                "ViGEmBus doit aussi être installé : "
                "https://github.com/ViGEm/ViGEmBus/releases"
            )
        except Exception as e:
            raise RuntimeError(
                f"Impossible de créer la manette virtuelle : {e}\n"
                "Vérifiez que ViGEmBus est installé et que vous avez les droits admin."
            )

        self.buttons  = Buttons()
        self.joystick = Joystick()

    # ── Application de l'état ─────────────────────────────────────────────────

    def apply(self) -> None:
        """
        Envoie l'état actuel de buttons et joystick à vgamepad.
        À appeler après chaque modification pour que la Driver Station
        voie les changements.
        """
        self._gamepad.reset()

        # ── Boutons ────────────────────────────────────────────────────────────
        for btn_name, vg_name in self._BUTTON_MAP.items():
            if self.buttons.getButtonState(btn_name):
                vg_btn = getattr(self._vg.XUSB_BUTTON, vg_name)
                self._gamepad.press_button(vg_btn)

        # ── Joysticks ──────────────────────────────────────────────────────────
        lx, ly = self.joystick.getLeftJoystick()
        rx, ry = self.joystick.getRightJoystick()
        # vgamepad attend Y positif = haut (même convention que nous)
        self._gamepad.left_joystick_float(x_value_float=lx,  y_value_float=ly)
        self._gamepad.right_joystick_float(x_value_float=rx, y_value_float=ry)

        # ── Gâchettes ──────────────────────────────────────────────────────────
        self._gamepad.left_trigger_float(self.joystick.getTriggerAxis("left"))
        self._gamepad.right_trigger_float(self.joystick.getTriggerAxis("right"))

        self._gamepad.update()

    def reset(self) -> None:
        """Remet tous les boutons et axes à zéro (sans appeler apply)."""
        self.buttons.setAllButtons(False)
        self.joystick.resetAll()

    def resetAndApply(self) -> None:
        """Reset complet + envoi immédiat à vgamepad."""
        self.reset()
        self.apply()

    # ── État global ───────────────────────────────────────────────────────────

    def getState(self) -> dict:
        """
        Retourne l'état complet de la manette sous forme de dictionnaire.

        Returns:
            {
                "buttons": {"A": bool, "B": bool, ...},
                "joystick": {"left_x": float, ..., "lt": float, "rt": float}
            }
        """
        return {
            "buttons":  self.buttons.getAllStates(),
            "joystick": self.joystick.getAllAxes(),
        }

    def __repr__(self) -> str:
        return (
            f"XboxController(\n"
            f"  {self.buttons!r}\n"
            f"  {self.joystick!r}\n"
            f")"
        )
