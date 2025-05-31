import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTextEdit, QLabel, QListWidgetItem, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt
import json
import sys

class AdbServiceViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📱 ADB Multi-Tool")
        self.resize(1100, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 14px;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: none;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #444;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 4px;
                color: #fff;
            }
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # Sol panel: servis listesi ve arama
        left_panel = QVBoxLayout()
        self.layout.addLayout(left_panel, 3)

        # Arama kutusu
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Servis Ara...")
        self.search_bar.textChanged.connect(self.filter_services)
        left_panel.addWidget(self.search_bar)

        # Servis listesi
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.show_service_details)
        left_panel.addWidget(self.list_widget)

        # Sağ panel: butonlar + detay metin alanı
        right_panel = QVBoxLayout()
        self.layout.addLayout(right_panel, 7)

        # Butonlar grid
        button_grid = QGridLayout()
        right_panel.addLayout(button_grid)

        self.connection_label = QLabel("🔌 Bağlantı: Bilinmiyor")
        right_panel.addWidget(self.connection_label)

        self.btn_check_connection = QPushButton("🔄 Cihaz Bağlantısını Kontrol Et")
        self.btn_check_connection.clicked.connect(self.check_connection)
        button_grid.addWidget(self.btn_check_connection, 0, 0)

        self.btn_load_services = QPushButton("📦 Servisleri Yükle")
        self.btn_load_services.clicked.connect(self.load_services)
        button_grid.addWidget(self.btn_load_services, 0, 1)

        self.btn_export = QPushButton("💾 Detayı Dışa Aktar")
        self.btn_export.clicked.connect(self.export_details)
        button_grid.addWidget(self.btn_export, 0, 2)

        self.btn_phone_info = QPushButton("📱 Telefon Bilgilerini Göster")
        self.btn_phone_info.clicked.connect(self.show_phone_info)
        button_grid.addWidget(self.btn_phone_info, 1, 0)

        self.btn_ip = QPushButton("🌐 IP Adresini Göster")
        self.btn_ip.clicked.connect(self.get_ip)
        button_grid.addWidget(self.btn_ip, 1, 1)

        self.btn_wifi = QPushButton("📶 Wi-Fi Ağlarını Tara")
        self.btn_wifi.clicked.connect(self.scan_wifi)
        button_grid.addWidget(self.btn_wifi, 1, 2)

        self.btn_bt = QPushButton("🔵 Bluetooth Cihazlarını Tara")
        self.btn_bt.clicked.connect(self.scan_bluetooth)
        button_grid.addWidget(self.btn_bt, 2, 0)

        # Detay alanı
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        right_panel.addWidget(self.details)

        self.service_items = []
        self.dark_mode = True

        self.check_connection()

    def run_adb_command(self, cmd_list):
        try:
            output = subprocess.check_output(
                cmd_list,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=15,
                errors="ignore"  # charset sorunlarını atlamak için
            )
            return output
        except subprocess.CalledProcessError as e:
            return f"Hata: Komut çalıştırılamadı.\n{e.output}"
        except subprocess.TimeoutExpired:
            return "Hata: Komut zaman aşımına uğradı."
        except Exception as e:
            return f"Hata: {e}"

    def check_connection(self):
        result = self.run_adb_command(["adb", "get-state"])
        if "device" in result:
            self.connection_label.setText("🔌 Bağlantı: Cihaz Bağlı")
        else:
            self.connection_label.setText("❌ Bağlantı: Cihaz Bağlı Değil")

    def load_services(self):
        self.details.clear()
        result = self.run_adb_command(["adb", "shell", "dumpsys"])
        services = [line.split("DUMP OF SERVICE ")[1].strip(":") for line in result.splitlines() if "DUMP OF SERVICE" in line]
        self.service_items.clear()
        self.list_widget.clear()
        for service in sorted(services):
            icon = "🎛️" if any(k in service for k in ["audio", "media", "power"]) else "📦"
            item = QListWidgetItem(f"{icon} {service}")
            item.setData(Qt.UserRole, service)
            self.list_widget.addItem(item)
            self.service_items.append(item)

    def filter_services(self, text):
        self.list_widget.clear()
        for item in self.service_items:
            if text.lower() in item.text().lower():
                self.list_widget.addItem(item)

    def show_service_details(self, item):
        service = item.data(Qt.UserRole)
        self.details.setText(f"📡 {service} servisi sorgulanıyor...")
        result = self.run_adb_command(["adb", "shell", "dumpsys", service])
        self.details.setText(result)

    def export_details(self):
        current_text = self.details.toPlainText()
        if not current_text.strip():
            QMessageBox.warning(self, "Uyarı", "Önce bir servis seçin veya bilgi getirin.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Dosya Kaydet", "detay.txt", "Tüm Dosyalar (*);;Metin Dosyası (*.txt);;JSON (*.json)")
        if path:
            try:
                if path.endswith(".json"):
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump({"details": current_text}, f, indent=2)
                else:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(current_text)
                QMessageBox.information(self, "Başarılı", "Veriler kaydedildi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {e}")

    def show_phone_info(self):
        self.details.clear()
        self.details.append("📱 Telefon bilgileri sorgulanıyor...\n")
        # Batarya durumu
        batarya = self.run_adb_command(["adb", "shell", "dumpsys", "battery"])
        self.details.append("🔋 Batarya Durumu:\n" + batarya)

        # Email bilgisi örneği (package com.android.email varsa)
        email_info = self.run_adb_command(["adb", "shell", "pm", "list", "packages", "email"])
        self.details.append("\n✉️ Email Paketi Durumu:\n" + email_info)

        # Telefon modeli ve versiyonu
        model = self.run_adb_command(["adb", "shell", "getprop", "ro.product.model"]).strip()
        version = self.run_adb_command(["adb", "shell", "getprop", "ro.build.version.release"]).strip()
        self.details.append(f"\n📱 Model: {model}")
        self.details.append(f"📱 Android Versiyon: {version}")

    def get_ip(self):
        self.details.clear()
        self.details.append("🌐 IP Adresi sorgulanıyor...\n")
        result = self.run_adb_command(["adb", "shell", "ip", "addr", "show"])
        self.details.append(result)

    def scan_wifi(self):
        self.details.clear()
        self.details.append("📶 Wi-Fi Ağları taraniyor...\n")
        result = self.run_adb_command(["adb", "shell", "dumpsys", "wifi"])
        self.details.append(result)

    def scan_bluetooth(self):
        self.details.clear()
        self.details.append("🔵 Bluetooth cihazları taraniyor...\n")
        result = self.run_adb_command(["adb", "shell", "hcitool", "scan"])
        self.details.append(result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = AdbServiceViewer()
    viewer.show()
    sys.exit(app.exec_())
