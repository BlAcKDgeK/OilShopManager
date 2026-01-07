from gui import OilShopApp
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OilShopApp()
    window.show()
    sys.exit(app.exec_())