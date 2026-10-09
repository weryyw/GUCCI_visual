from pathlib import Path
import os
import sys
import subprocess
import threading
import traceback
import uuid
import re

import minecraft_launcher_lib

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QProgressBar,
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MINECRAFT_DIR = BASE_DIR / ".minecraft"
MODS_DIR = BASE_DIR / "mods"

GUCCI_JAR = MODS_DIR / "GUCCI_visual.jar"

MINECRAFT_VERSION = "1.21.11"

LAUNCHER_NAME = "GUCCI_visual"
LAUNCHER_VERSION = "1.0"

OFFLINE_TOKEN = "00000000000000000000000000000000"


# ============================================================
# ОСНОВНОЕ ОКНО
# ============================================================

class Launcher(QWidget):

    status_signal = Signal(str)
    progress_signal = Signal(int)
    error_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GUCCI_visual")
        self.setFixedSize(650, 400)

        self.setStyleSheet("""
            QWidget {
                background: #101010;
                color: #ffffff;
                font-family: Segoe UI;
            }

            QLabel#title {
                color: #d1a64c;
                font-size: 32px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #777777;
                font-size: 13px;
            }

            QLabel#status {
                color: #aaaaaa;
                font-size: 13px;
            }

            QLineEdit {
                background: #181818;
                border: 1px solid #333333;
                color: white;
                padding: 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #b58b3e;
            }

            QPushButton {
                background: #b58b3e;
                color: #111111;
                border: none;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #d0aa58;
            }

            QPushButton:disabled {
                background: #444444;
                color: #888888;
            }

            QProgressBar {
                background: #181818;
                border: 1px solid #333333;
                height: 8px;
            }

            QProgressBar::chunk {
                background: #b58b3e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setSpacing(15)

        title = QLabel("GUCCI_visual")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Minecraft Fabric Launcher • Minecraft 1.21.11"
        )
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(15)

        self.nickname = QLineEdit()
        self.nickname.setText("Player")
        self.nickname.setPlaceholderText("Minecraft никнейм")
        layout.addWidget(self.nickname)

        self.status = QLabel("Готов к запуску")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        layout.addSpacing(10)

        self.play_button = QPushButton("ИГРАТЬ")
        self.play_button.clicked.connect(self.start)
        layout.addWidget(self.play_button)

        info = QLabel(
            "GUCCI_visual.jar загружается из папки mods.\n"
            "Gradle не используется."
        )

        info.setStyleSheet(
            "color: #555555; font-size: 11px;"
        )

        layout.addWidget(info)

        self.status_signal.connect(self.status.setText)
        self.progress_signal.connect(self.progress.setValue)
        self.error_signal.connect(self.show_error)
        self.finished_signal.connect(self.enable_button)

    # ========================================================
    # ПРОВЕРКА JAR
    # ========================================================

    def check_gucci(self):

        MODS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        if not GUCCI_JAR.exists():

            raise FileNotFoundError(
                "Не найден GUCCI_visual.jar\n\n"
                "Файл должен находиться здесь:\n\n"
                f"{GUCCI_JAR}"
            )

        if GUCCI_JAR.stat().st_size < 10000:

            raise RuntimeError(
                "GUCCI_visual.jar слишком маленький "
                "и, возможно, повреждён."
            )

    # ========================================================
    # ЗАПУСК
    # ========================================================

    def start(self):

        username = self.nickname.text().strip()

        if not re.fullmatch(
            r"[A-Za-z0-9_]{3,16}",
            username
        ):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Ник должен содержать 3–16 символов:\n"
                "латинские буквы, цифры и _"
            )
            return

        if not self.play_button.isEnabled():
            return

        self.play_button.setEnabled(False)

        threading.Thread(
            target=self.launch,
            args=(username,),
            daemon=True
        ).start()

    # ========================================================
    # ОСНОВНОЙ LAUNCH
    # ========================================================

    def launch(self, username):

        try:

            # ------------------------------------------------
            # 1. Проверяем готовый клиент
            # ------------------------------------------------

            self.set_status(
                "Проверяю GUCCI_visual.jar..."
            )

            self.set_progress(5)

            self.check_gucci()

            # ------------------------------------------------
            # 2. Создаём директории
            # ------------------------------------------------

            MINECRAFT_DIR.mkdir(
                parents=True,
                exist_ok=True
            )

            MODS_DIR.mkdir(
                parents=True,
                exist_ok=True
            )

            # ------------------------------------------------
            # 3. Ничего не компилируем.
            # Просто убеждаемся, что JAR находится в mods.
            # ------------------------------------------------

            target_jar = (
                MINECRAFT_DIR /
                "mods" /
                "GUCCI_visual.jar"
            )

            target_jar.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Копируем готовый JAR в настоящий .minecraft/mods
            target_jar.write_bytes(
                GUCCI_JAR.read_bytes()
            )

            self.set_status(
                "GUCCI_visual.jar установлен."
            )

            self.set_progress(15)

            # ------------------------------------------------
            # 4. Minecraft
            # ------------------------------------------------

            self.set_status(
                "Проверяю Minecraft..."
            )

            versions = (
                minecraft_launcher_lib
                .utils
                .get_installed_versions(
                    str(MINECRAFT_DIR)
                )
            )

            version_ids = {
                item["id"]
                for item in versions
            }

            if MINECRAFT_VERSION not in version_ids:

                self.set_status(
                    "Устанавливаю Minecraft 1.21.11..."
                )

                minecraft_launcher_lib.install.install_minecraft_version(
                    MINECRAFT_VERSION,
                    str(MINECRAFT_DIR),
                    callback={
                        "setStatus": self.minecraft_status,
                        "setProgress": self.minecraft_progress
                    }
                )

            self.set_progress(40)

            # ------------------------------------------------
            # 5. Java runtime
            # ------------------------------------------------

            self.set_status(
                "Проверяю Java..."
            )

            runtime_info = (
                minecraft_launcher_lib.runtime
                .get_version_runtime_information(
                    MINECRAFT_VERSION,
                    str(MINECRAFT_DIR)
                )
            )

            java_path = None

            if runtime_info:

                runtime_name = runtime_info["name"]

                self.set_status(
                    f"Java runtime: {runtime_name}"
                )

                minecraft_launcher_lib.runtime.install_jvm_runtime(
                    runtime_name,
                    str(MINECRAFT_DIR),
                    callback={
                        "setStatus": self.minecraft_status,
                        "setProgress": self.minecraft_progress
                    }
                )

                java_path = (
                    minecraft_launcher_lib.runtime
                    .get_executable_path(
                        runtime_name,
                        str(MINECRAFT_DIR)
                    )
                )

            self.set_progress(60)

            # ------------------------------------------------
            # 6. Fabric
            # ------------------------------------------------

            self.set_status(
                "Проверяю Fabric..."
            )

            versions = (
                minecraft_launcher_lib
                .utils
                .get_installed_versions(
                    str(MINECRAFT_DIR)
                )
            )

            fabric_version = None

            for version in versions:

                vid = version.get("id", "")

                if (
                    vid.startswith("fabric-loader-")
                    and vid.endswith(
                        "-" + MINECRAFT_VERSION
                    )
                ):
                    fabric_version = vid
                    break

            # Если Fabric ещё нет — устанавливаем.
            if fabric_version is None:

                self.set_status(
                    "Устанавливаю Fabric..."
                )

                minecraft_launcher_lib.fabric.install_fabric(
                    MINECRAFT_VERSION,
                    str(MINECRAFT_DIR)
                )

                versions = (
                    minecraft_launcher_lib
                    .utils
                    .get_installed_versions(
                        str(MINECRAFT_DIR)
                    )
                )

                for version in versions:

                    vid = version.get("id", "")

                    if (
                        vid.startswith("fabric-loader-")
                        and vid.endswith(
                            "-" + MINECRAFT_VERSION
                        )
                    ):
                        fabric_version = vid
                        break

            if fabric_version is None:

                raise RuntimeError(
                    "Fabric не найден после установки.\n\n"
                    "Проверь папку:\n"
                    f"{MINECRAFT_DIR / 'versions'}"
                )

            self.set_status(
                f"Fabric найден: {fabric_version}"
            )

            self.set_progress(75)

            # ------------------------------------------------
            # 7. Параметры игрока
            # ------------------------------------------------

            options = {
                "username": username,
                "uuid": str(uuid.uuid4()),
                "token": OFFLINE_TOKEN,
                "launcherName": LAUNCHER_NAME,
                "launcherVersion": LAUNCHER_VERSION
            }

            if java_path and Path(java_path).exists():

                options["executablePath"] = java_path

            # ------------------------------------------------
            # 8. Получаем команду Minecraft
            # ------------------------------------------------

            self.set_status(
                "Формирую команду запуска..."
            )

            command = (
                minecraft_launcher_lib.command
                .get_minecraft_command(
                    fabric_version,
                    str(MINECRAFT_DIR),
                    options
                )
            )

            self.set_progress(90)

            # ------------------------------------------------
            # 9. ЗАПУСК
            # ------------------------------------------------

            self.set_status(
                "Запускаю Minecraft..."
            )

            print()
            print("=" * 60)
            print("GUCCI_visual")
            print("=" * 60)
            print("Minecraft:", MINECRAFT_VERSION)
            print("Fabric:", fabric_version)
            print("Java:", java_path)
            print("Mods:", MINECRAFT_DIR / "mods")
            print("=" * 60)

            process = subprocess.Popen(
                command,
                cwd=str(MINECRAFT_DIR)
            )

            print(
                f"Minecraft PID: {process.pid}"
            )

            self.set_progress(100)

            self.set_status(
                "Minecraft запущен."
            )

        except Exception:

            error = traceback.format_exc()

            print(error)

            self.error_signal.emit(
                error
            )

        finally:

            self.finished_signal.emit()

    # ========================================================
    # CALLBACKS
    # ========================================================

    def set_status(self, text):

        self.status_signal.emit(
            str(text)
        )

    def set_progress(self, value):

        try:

            value = int(value)

        except Exception:

            return

        self.progress_signal.emit(
            max(0, min(100, value))
        )

    def minecraft_status(self, text):

        self.set_status(
            text
        )

    def minecraft_progress(self, value):

        try:

            value = int(float(value))
            self.set_progress(value)

        except Exception:

            pass

    # ========================================================
    # ОШИБКА
    # ========================================================

    def show_error(self, error):

        self.status.setText(
            "Ошибка запуска"
        )

        QMessageBox.critical(
            self,
            "GUCCI_visual — ошибка",
            error
        )

    # ========================================================
    # ГОТОВО
    # ========================================================

    def enable_button(self):

        self.play_button.setEnabled(
            True
        )


# ============================================================
# START
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    window = Launcher()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()