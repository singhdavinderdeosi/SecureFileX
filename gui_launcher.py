from PyQt5.QtWidgets import QApplication, QLabel, QWidget

app = QApplication([])
window = QWidget()
window.setWindowTitle("Hello PyQt5")
window.setGeometry(100, 100, 280, 80)
label = QLabel("<h1>Hello World!</h1>", parent=window)
label.move(60, 15)
window.show()
app.exec_()
