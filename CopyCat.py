import sys
import json
import os  # <-- ADDED
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit,
    QScrollArea, QGridLayout, QHBoxLayout, QVBoxLayout, QDialog, QFrame,
    QSizePolicy, QCheckBox, QStyle, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QByteArray,
    QStandardPaths
)
from PySide6.QtGui import QClipboard, QIcon, QIntValidator

# --- Global constant for the save file ---
# Get the user's standard data directory
app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)

# We'll create a folder inside it for our app
app_data_dir = os.path.join(app_data_dir, "CopyCat") 

# Create the directory if it doesn't exist
if not os.path.exists(app_data_dir):
    try:
        os.makedirs(app_data_dir)
    except OSError as e:
        print(f"Error creating AppData directory: {e}")
        
# The full, correct path to our data file
DATA_FILE = os.path.join(app_data_dir, "sentences.json")
print(f"Data file location: {DATA_FILE}")


# <--- NEW FUNCTION ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# --- END OF NEW FUNCTION ---


# --- 1. Custom Widget for each Sentence Card ---
class SentenceCard(QFrame):
    delete_requested = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text_content = text
        self.setObjectName("SentenceCard")
        
        # View Mode Widgets
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon.fromTheme("edit-copy", QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        self.copy_btn.setObjectName("CopyButton")
        self.copy_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding) 
        
        # Edit Mode Widgets
        self.order_entry = QLineEdit()
        self.order_entry.setObjectName("OrderEntry")
        self.order_entry.setValidator(QIntValidator(0, 999))
        self.order_entry.setFixedWidth(40)
        self.edit_entry = QLineEdit(text)
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.delete_btn.setObjectName("DeleteButton")
        self.delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.addWidget(self.order_entry) 
        self.layout.addWidget(self.edit_entry, 1) 
        self.layout.addWidget(self.delete_btn)
        self.order_entry.hide() 
        self.edit_entry.hide()
        self.delete_btn.hide()
        self.layout.addWidget(self.label, 1)
        self.layout.addWidget(self.copy_btn, 0)
        
        # Flash Animation Overlay
        self.flash_overlay = QFrame(self)
        self.flash_overlay.setObjectName("FlashOverlay")
        self.flash_overlay.lower() 
        self.opacity_effect = QGraphicsOpacityEffect(self.flash_overlay)
        self.flash_overlay.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        self.flash_animation = QPropertyAnimation(self.opacity_effect, QByteArray(b"opacity"))
        self.flash_animation.setDuration(400) 
        self.flash_animation.setStartValue(0.0)
        self.flash_animation.setKeyValueAt(0.1, 0.8) 
        self.flash_animation.setEndValue(0.0)
        self.flash_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Connect Signals
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.delete_btn.clicked.connect(self.delete_requested.emit)

    def mousePressEvent(self, event):
        if self.label.isVisible():
            if not self.copy_btn.geometry().contains(event.pos()):
                self.copy_to_clipboard() 
        super().mousePressEvent(event)
    
    def resizeEvent(self, event):
        self.flash_overlay.resize(event.size())
        super().resizeEvent(event)
        
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_content)
        print(f"Copied: {self.text_content}")
        self.flash_animation.start()

    def setEditMode(self, is_edit):
        if is_edit:
            self.order_entry.show()
            self.edit_entry.show()
            self.delete_btn.show()
            self.edit_entry.setText(self.text_content)
            self.label.hide()
            self.copy_btn.hide()
        else:
            self.order_entry.hide()
            self.edit_entry.hide()
            self.delete_btn.hide()
            self.label.show()
            self.copy_btn.show()

    def get_text_from_entry(self):
        return self.edit_entry.text()
    
    def get_order_number(self):
        try:
            return int(self.order_entry.text())
        except ValueError:
            return 999 
    
    def set_order_number(self, num):
        self.order_entry.setText(str(num))

    def set_text(self, text):
        self.text_content = text
        self.label.setText(text)
        self.edit_entry.setText(text)

# --- 2. 'Add Sentence' Pop-up Dialog ---
class AddSentenceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Sentence")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setObjectName("AddDialog")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Enter sentence here...")
        self.entry.setObjectName("DialogEntry")
        self.layout.addWidget(self.entry)
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("DialogSaveButton")
        self.layout.addWidget(self.save_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.save_btn.clicked.connect(self.accept)
        self.entry.returnPressed.connect(self.accept)
    def get_text(self):
        return self.entry.text()

# --- 3. Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CopyCat by chamirurf") 
        
        # <--- MODIFIED LINES ---
        icon_path = resource_path("CopyCat.ico")
        self.setWindowIcon(QIcon(icon_path))
        # --- END OF MODIFIED LINES ---
        
        self.setGeometry(100, 100, 850, 600)
        self.sentence_widgets = [] 
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setCentralWidget(main_widget)
        
        # --- Top Bar ---
        top_bar_widget = QWidget()
        top_bar_layout = QHBoxLayout(top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.add_btn = QPushButton("Add")
        self.edit_mode_check = QCheckBox("Edit Mode")
        self.save_edits_btn = QPushButton("Save Edits")
        self.cancel_edits_btn = QPushButton("Cancel")
        self.clear_clipboard_btn = QPushButton("Clear Clipboard")
        self.add_btn.setObjectName("AddButton")
        self.save_edits_btn.setObjectName("SaveButton")
        self.cancel_edits_btn.setObjectName("CancelButton")
        top_bar_layout.addWidget(self.add_btn)
        top_bar_layout.addWidget(self.edit_mode_check)
        top_bar_layout.addWidget(self.save_edits_btn)
        top_bar_layout.addWidget(self.cancel_edits_btn)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(self.clear_clipboard_btn)
        self.save_edits_btn.hide()
        self.cancel_edits_btn.hide()
        main_layout.addWidget(top_bar_widget)

        # --- Scroll Area for Sentences ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ScrollArea")
        self.scroll_content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.scroll_content_widget)
        self.content_layout.setSpacing(8)
        self.column_1_layout = QVBoxLayout()
        self.column_1_layout.setSpacing(8)
        self.column_2_layout = QVBoxLayout()
        self.column_2_layout.setSpacing(8)
        self.content_layout.addLayout(self.column_1_layout, 1)
        self.content_layout.addLayout(self.column_2_layout, 1)
        self.column_1_layout.addStretch(1)
        self.column_2_layout.addStretch(1)
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area, 1) # '1' stretch
        
        # <--- Placeholder Label ---
        self.placeholder_label = QLabel("Click 'Add' to get started!")
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.placeholder_label, 1) # '1' stretch

        # --- Connect Signals ---
        self.add_btn.clicked.connect(self.open_add_prompt)
        self.edit_mode_check.toggled.connect(self.toggle_edit_mode)
        self.save_edits_btn.clicked.connect(self.save_edits)
        self.cancel_edits_btn.clicked.connect(self.cancel_edits)
        self.clear_clipboard_btn.clicked.connect(self.clear_clipboard)

        # --- Apply Stylesheet ---
        self.apply_stylesheet()
        
        # --- Load Data ---
        self.load_data()
        
        # --- Initial check for empty state ---
        self.check_empty_state() 


    def open_add_prompt(self):
        dialog = AddSentenceDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                self.add_sentence_card(text)
                self.save_data() 
                self.check_empty_state() 

    def add_sentence_card(self, text):
        card = SentenceCard(text)
        card.delete_requested.connect(self.delete_sentence)
        
        if self.column_1_layout.sizeHint().height() <= self.column_2_layout.sizeHint().height():
            self.column_1_layout.insertWidget(self.column_1_layout.count() - 1, card)
        else:
            self.column_2_layout.insertWidget(self.column_2_layout.count() - 1, card)
            
        self.sentence_widgets.append(card)
        card.set_order_number(len(self.sentence_widgets) - 1)
        card.setEditMode(self.edit_mode_check.isChecked())


    def toggle_edit_mode(self, is_edit):
        if is_edit:
            self.save_edits_btn.show()
            self.cancel_edits_btn.show()
            for i, card in enumerate(self.sentence_widgets):
                card.set_order_number(i)
                card.setEditMode(True)
        else:
            self.save_edits_btn.hide()
            self.cancel_edits_btn.hide()
            for card in self.sentence_widgets:
                card.setEditMode(False)

    def save_edits(self):
        card_data = []
        for card in self.sentence_widgets:
            order = card.get_order_number()
            text = card.get_text_from_entry()
            card_data.append((order, text, card))

        card_data.sort(key=lambda x: x[0])
        self.sentence_widgets.clear()
        for order, text, card in card_data:
            card.set_text(text)
            self.sentence_widgets.append(card)
        
        self.save_data()
        self.rebuild_layout()
        self.edit_mode_check.setChecked(False)

    def cancel_edits(self):
        for card in self.sentence_widgets:
            card.set_text(card.text_content) 
        self.edit_mode_check.setChecked(False)

    def clear_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.clear()
        print("Clipboard cleared")

    def load_data(self):
        try:
            with open(DATA_FILE, "r") as f:
                sentences = json.load(f)
            if isinstance(sentences, list):
                for text in sentences:
                    self.add_sentence_card(str(text))
        
        except (FileNotFoundError, json.JSONDecodeError):
            print("No data file found, starting empty.")
            # No default sentences are loaded

    def save_data(self):
        sentences_list = [card.text_content for card in self.sentence_widgets]
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(sentences_list, f, indent=4)
            print("Data saved.")
        except IOError as e:
            print(f"Error saving data: {e}")

    def delete_sentence(self):
        card_to_delete = self.sender()
        if card_to_delete in self.sentence_widgets:
            self.sentence_widgets.remove(card_to_delete) 
            card_to_delete.deleteLater()                 
            self.save_data()                             
            print("Sentence deleted.")
            self.rebuild_layout()
            self.check_empty_state() 

    def rebuild_layout(self):
        for card in self.sentence_widgets:
            card.setParent(None)
            
        for i, card in enumerate(self.sentence_widgets):
            if self.column_1_layout.sizeHint().height() <= self.column_2_layout.sizeHint().height():
                self.column_1_layout.insertWidget(self.column_1_layout.count() - 1, card)
            else:
                self.column_2_layout.insertWidget(self.column_2_layout.count() - 1, card)
            
            card.set_order_number(i)
            card.setEditMode(self.edit_mode_check.isChecked())
            
    
    def check_empty_state(self):
        """Shows or hides the placeholder based on if sentences exist."""
        if len(self.sentence_widgets) == 0:
            self.scroll_area.hide()
            self.placeholder_label.show()
        else:
            self.scroll_area.show()
            self.placeholder_label.hide()


    
    def apply_stylesheet(self):
        """Applies the QSS (CSS-like) stylesheet to the application."""
        style = """
        /* --- Main Window --- */
        QMainWindow, QWidget {
            background-color: #000000; color: #F0F0F0;
            font-family: Inter, Segoe UI, sans-serif; font-size: 10pt;
        }
        /* --- Top Bar Buttons --- */
        QPushButton {
            background-color: #2A2A2A; color: #F0F0F0;
            border: 1px solid #333333; border-radius: 8px;
            padding: 8px 16px; font-weight: 500;
        }
        QPushButton:hover { background-color: #3A3A3A; }
        QPushButton:pressed { background-color: #4A4A4A; }
        /* --- Special Buttons (Add, Save) --- */
        QPushButton#AddButton, QPushButton#SaveButton {
            background-color: #007AFF; color: white; border: none;
        }
        QPushButton#AddButton:hover, QPushButton#SaveButton:hover {
            background-color: #006DE0;
        }
        QPushButton#CancelButton {
            background-color: #333333; color: #F0F0F0; border: none;
        }
        /* --- Edit Mode Checkbox --- */
        QCheckBox {
            spacing: 8px; padding: 8px 0; color: #F0F0F0;
        }
        QCheckBox::indicator { width: 20px; height: 20px; }
        
        /* --- Scroll Area --- */
        QScrollArea { border: none; }
        QScrollArea QWidget { background-color: transparent; }

        /* --- Scroll Bar --- */
        QScrollBar:vertical {
            border: none; background-color: #000000;
            width: 10px; margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #3A3A3A; border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background-color: #5A5A5A; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none; background: none; height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            border: none; background-color: #000000;
            height: 10px; margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: #3A3A3A; border-radius: 5px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover { background-color: #5A5A5A; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none; background: none; width: 0px;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }

        /* --- Sentence Card --- */
        QFrame#SentenceCard {
            background-color: #1C1C1C; border-radius: 12px;
            border: 1px solid #333333;
        }
        QLabel { background-color: transparent; color: #F0F0F0; }
        
        /* --- NEW: Placeholder Label --- */
        QLabel#PlaceholderLabel {
            color: #555555; /* Muted text */
            font-size: 14pt;
        }
        
        /* --- Flash Overlay --- */
        QFrame#FlashOverlay {
            background-color: #FFFFFF; border-radius: 12px; border: none;
        }
        
        /* --- Card Buttons --- */
        QPushButton#CopyButton {
            background-color: #3A4C5F; color: #79B8FF;
            font-weight: 600; border: none;
            padding: 8px 10px; border-radius: 6px;

        }
        QPushButton#CopyButton:hover { background-color: #4A5C6F; }
                
        QPushButton#DeleteButton {
            background-color: #5C2B2B; color: #FF8A8A;
            border: none; padding: 8px 10px; border-radius: 6px;
        }
        QPushButton#DeleteButton:hover { background-color: #7C3B3B; }

        /* --- Text Input Fields --- */
        QLineEdit {
            background-color: #1A1A1A; border: 1px solid #333333;
            border-radius: 8px; padding: 8px 12px;
            font-size: 10pt; color: #F0F0F0;
        }
        QLineEdit:focus { border: 1px solid #007AFF; }
        
        QLineEdit#OrderEntry {
            background-color: #2A2A2A;
            padding: 8px 4px;
            text-align: center;
        }

        /* --- Add Sentence Dialog --- */
        QDialog#AddDialog { background-color: #000000; }
        QLineEdit#DialogEntry { font-size: 11pt; padding: 12px; }
        QPushButton#DialogSaveButton {
            background-color: #007AFF; color: white; border: none;
            font-weight: 600; padding: 10px 20px;
        }
        QPushButton#DialogSaveButton:hover { background-color: #006DE0; }
        """
        self.setStyleSheet(style)


# --- 4. Run the Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())