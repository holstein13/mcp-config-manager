import sys
from PyQt6.QtWidgets import QApplication, QWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('PyQt6 Test')
    window.show()
    sys.exit(app.exec())
