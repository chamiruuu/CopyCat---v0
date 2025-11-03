import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit,
    QScrollArea, QGridLayout, QHBoxLayout, QVBoxLayout, QDialog, QFrame,
    QSizePolicy, QCheckBox, QStyle, QGraphicsOpacityEffect, QMenu
)
from PySide6.QtCore import (
    Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, QByteArray,
    QStandardPaths, QMimeData
)
from PySide6.QtGui import (
    QClipboard, QIcon, QIntValidator, QDrag, QPixmap, 
    QPainter, QColor, QCursor
)

# --- Global constant for the save file ---
# (Unchanged)
app_data_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
app_data_dir = os.path.join(app_data_dir, "CopyCat") 
if not os.path.exists(app_data_dir):
    try:
        os.makedirs(app_data_dir)
    except OSError as e:
        print(f"Error creating AppData directory: {e}")
DATA_FILE = os.path.join(app_data_dir, "sentences.json")
print(f"Data file location: {DATA_FILE}")

# --- (Unchanged)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- 1. Custom Widget for each Sentence Card ---
# <--- HEAVILY MODIFIED: REMOVED DRAG/DROP, ADDED BUTTONS --->
class SentenceCard(QFrame):
    delete_requested = Signal()
    # --- NEW SIGNALS ---
    move_up_requested = Signal()
    move_down_requested = Signal()
    switch_col_requested = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text_content = text
        self.setObjectName("SentenceCard")
        
        # --- REMOVED Drag Handle and mouse events ---
        
        # View Mode Widgets
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon.fromTheme("edit-copy", QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        self.copy_btn.setObjectName("CopyButton")
        self.copy_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding) 
        
        # Edit Mode Widgets
        self.edit_entry = QLineEdit(text)
        
        # --- NEW Reorder Buttons ---
        self.move_up_btn = QPushButton("▲")
        self.move_up_btn.setObjectName("MoveUpButton")
        self.move_up_btn.setFixedSize(30, 30)
        self.move_up_btn.setToolTip("Move Up")
        
        self.move_down_btn = QPushButton("▼")
        self.move_down_btn.setObjectName("MoveDownButton")
        self.move_down_btn.setFixedSize(30, 30)
        self.move_down_btn.setToolTip("Move Down")

        self.switch_col_btn = QPushButton("↔")
        self.switch_col_btn.setObjectName("SwitchColButton")
        self.switch_col_btn.setFixedSize(30, 30)
        self.switch_col_btn.setToolTip("Switch Column")
        
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.delete_btn.setObjectName("DeleteButton")
        self.delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        # --- Edit Mode Layout ---
        self.edit_widget = QWidget() # Container for edit items
        self.edit_layout = QHBoxLayout(self.edit_widget)
        self.edit_layout.setContentsMargins(0, 0, 0, 0)
        self.edit_layout.addWidget(self.edit_entry, 1)
        self.edit_layout.addWidget(self.move_up_btn)
        self.edit_layout.addWidget(self.move_down_btn)
        self.edit_layout.addWidget(self.switch_col_btn)
        self.edit_layout.addWidget(self.delete_btn)
        self.layout.addWidget(self.edit_widget)
        self.edit_widget.hide()

        # --- View Mode Layout ---
        self.view_widget = QWidget() # Container for view items
        self.view_layout = QHBoxLayout(self.view_widget)
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        self.view_layout.addWidget(self.label, 1)
        self.view_layout.addWidget(self.copy_btn, 0)
        self.layout.addWidget(self.view_widget)
        self.view_widget.show()
        
        # Flash Animation Overlay (Unchanged)
        self.flash_overlay = QFrame(self)
        self.flash_overlay.setObjectName("FlashOverlay")
        self.flash_overlay.lower() 
        self.opacity_effect = QGraphicsOpacityEffect(self.flash_overlay)
        # ... (rest of animation setup is unchanged) ...
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
        # --- NEW Connections ---
        self.move_up_btn.clicked.connect(self.move_up_requested.emit)
        self.move_down_btn.clicked.connect(self.move_down_requested.emit)
        self.switch_col_btn.clicked.connect(self.switch_col_requested.emit)

    def mousePressEvent(self, event):
        # --- MODIFIED: Simplified to only copy ---
        if event.button() == Qt.MouseButton.LeftButton:
            if self.view_widget.isVisible():
                if not self.copy_btn.geometry().contains(event.pos()):
                    self.copy_to_clipboard() 
        super().mousePressEvent(event)
    
    # --- REMOVED mouseMoveEvent and mouseReleaseEvent ---

    def resizeEvent(self, event):
        # (Unchanged)
        self.flash_overlay.resize(event.size())
        super().resizeEvent(event)
        
    def copy_to_clipboard(self):
        # (Unchanged)
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_content)
        print(f"Copied: {self.text_content}")
        self.flash_animation.start()

    def setEditMode(self, is_edit):
        # --- MODIFIED: Show/hide widgets ---
        if is_edit:
            self.edit_widget.show()
            self.view_widget.hide()
            self.edit_entry.setText(self.text_content)
        else:
            self.edit_widget.hide()
            self.view_widget.show()
            # Save text changes when switching off
            self.text_content = self.edit_entry.text()
            self.label.setText(self.text_content)

    def get_text_from_entry(self):
        # (Unchanged)
        return self.edit_entry.text()
    
    def set_text(self, text):
        # (Unchanged)
        self.text_content = text
        self.label.setText(text)
        self.edit_entry.setText(text)


# --- 2. 'Add Sentence' Pop-up Dialog ---
# (Unchanged)
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


# --- 3. DropColumn Class REMOVED ---


# --- 4. Main Application Window ---
# <--- HEAVILY MODIFIED: REMOVED DRAG/DROP, ADDED BUTTON HANDLERS --->
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CopyCat by chamirurf") 
        icon_path = resource_path("CopyCat.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 850, 600)
        
        self.column_1_widgets = [] 
        self.column_2_widgets = []
        # --- REMOVED self.dragged_card ---
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setCentralWidget(main_widget)
        
        # --- Top Bar (Unchanged) ---
        top_bar_widget = QWidget()
        top_bar_layout = QHBoxLayout(top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.add_btn = QPushButton("Add")
        self.edit_mode_check = QCheckBox("Edit Mode")
        self.clear_clipboard_btn = QPushButton("Clear Clipboard")
        self.add_btn.setObjectName("AddButton")
        top_bar_layout.addWidget(self.add_btn)
        top_bar_layout.addWidget(self.edit_mode_check)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(self.clear_clipboard_btn)
        main_layout.addWidget(top_bar_widget)

        # --- Scroll Area for Sentences ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ScrollArea")
        self.scroll_content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.scroll_content_widget)
        self.content_layout.setSpacing(8)
        
        # --- MODIFIED: Use standard QVBoxLayouts ---
        self.column_1_widget = QWidget()
        self.column_1_layout = QVBoxLayout(self.column_1_widget)
        self.column_1_layout.setContentsMargins(0, 0, 0, 0)
        self.column_1_layout.setSpacing(8)
        self.column_1_layout.addStretch(1) 
        
        self.column_2_widget = QWidget()
        self.column_2_layout = QVBoxLayout(self.column_2_widget)
        self.column_2_layout.setContentsMargins(0, 0, 0, 0)
        self.column_2_layout.setSpacing(8)
        self.column_2_layout.addStretch(1)

        self.content_layout.addWidget(self.column_1_widget, 1)
        self.content_layout.addWidget(self.column_2_widget, 1)
        # ---
        
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area, 1)
        
        self.placeholder_label = QLabel("Click 'Add' to get started!")
        self.placeholder_label.setObjectName("PlaceholderLabel")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.placeholder_label, 1) 

        # --- Connect Signals ---
        self.add_btn.clicked.connect(self.open_add_prompt)
        self.edit_mode_check.toggled.connect(self.toggle_edit_mode)
        self.clear_clipboard_btn.clicked.connect(self.clear_clipboard)
        
        # --- REMOVED drop signals ---

        self.apply_stylesheet()
        self.load_data()
        self.check_empty_state() 

    def open_add_prompt(self):
        dialog = AddSentenceDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            if text:
                # --- MODIFIED: Call with column_index=-1 for auto-balance ---
                self.add_sentence_card(text, column_index=-1)
                self.save_data() 
                self.check_empty_state() 

    def add_sentence_card(self, text, column_index, widget_index=-1):
        """Adds a card to a specific column/index or auto-balances."""
        card = SentenceCard(text)
        # --- NEW Connections ---
        card.delete_requested.connect(self.delete_sentence)
        card.move_up_requested.connect(self.on_move_up)
        card.move_down_requested.connect(self.on_move_down)
        card.switch_col_requested.connect(self.on_switch_col)
        
        target_layout = None
        target_list = None
        
        if column_index == 0:
            target_layout = self.column_1_layout
            target_list = self.column_1_widgets
        elif column_index == 1:
            target_layout = self.column_2_layout
            target_list = self.column_2_widgets
        else:
            # Auto-balance
            if self.column_1_layout.sizeHint().height() <= self.column_2_layout.sizeHint().height():
                target_layout = self.column_1_layout
                target_list = self.column_1_widgets
            else:
                target_layout = self.column_2_layout
                target_list = self.column_2_widgets
        
        if widget_index == -1 or widget_index > len(target_list):
            # Add to end (before stretcher)
            widget_index = target_layout.count() - 1 
            
        target_layout.insertWidget(widget_index, card)
        target_list.insert(widget_index, card)
            
        card.setEditMode(self.edit_mode_check.isChecked())
        return card

    def toggle_edit_mode(self, is_edit):
        if not is_edit:
            # When turning edit mode *off*, save text changes
            self.save_edits()
            
        for card in self.get_all_widgets():
            card.setEditMode(is_edit)

    def save_edits(self):
        """Saves text changes from edit fields. Does NOT reorder."""
        for card in self.get_all_widgets():
            card.set_text(card.get_text_from_entry())
        self.save_data()
        print("Text edits saved.")

    def clear_clipboard(self):
        # (Unchanged)
        clipboard = QApplication.clipboard()
        clipboard.clear()
        print("Clipboard cleared")

    def load_data(self):
        # (Unchanged, but logic now works with new add_sentence_card)
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                col1_sentences = data.get("col1", [])
                col2_sentences = data.get("col2", [])
                
                for i, text in enumerate(col1_sentences):
                    self.add_sentence_card(str(text), column_index=0, widget_index=i)
                for i, text in enumerate(col2_sentences):
                    self.add_sentence_card(str(text), column_index=1, widget_index=i)
            
            elif isinstance(data, list): # Legacy support
                for text in data:
                    self.add_sentence_card(str(text), column_index=-1) # Auto-balance
                self.save_data() # Re-save in new format
        
        except (FileNotFoundError, json.JSONDecodeError):
            print("No data file found, starting empty.")

    def save_data(self):
        # (Unchanged)
        data_to_save = {
            "col1": [card.text_content for card in self.column_1_widgets],
            "col2": [card.text_content for card in self.column_2_widgets]
        }
        
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(data_to_save, f, indent=4)
            print("Data saved.")
        except IOError as e:
            print(f"Error saving data: {e}")

    def delete_sentence(self):
        # (Unchanged)
        card_to_delete = self.sender()
        if card_to_delete in self.column_1_widgets:
            self.column_1_widgets.remove(card_to_delete)
        elif card_to_delete in self.column_2_widgets:
            self.column_2_widgets.remove(card_to_delete)
        else:
            return 

        card_to_delete.deleteLater() 
        self.save_data()                             
        print("Sentence deleted.")
        self.check_empty_state() 
            
    def check_empty_state(self):
        # (Unchanged)
        if not self.get_all_widgets():
            self.scroll_area.hide()
            self.placeholder_label.show()
        else:
            self.scroll_area.show()
            self.placeholder_label.hide()
            
    def get_all_widgets(self):
        # (Unchanged)
        return self.column_1_widgets + self.column_2_widgets
        
    # --- NEW Button Handlers ---
    def on_move_up(self):
        card = self.sender()
        
        target_list, target_layout = None, None
        if card in self.column_1_widgets:
            target_list, target_layout = self.column_1_widgets, self.column_1_layout
        elif card in self.column_2_widgets:
            target_list, target_layout = self.column_2_widgets, self.column_2_layout
        else:
            return # Should not happen

        index = target_list.index(card)
        if index > 0: # Can move up
            # Swap in list
            target_list[index], target_list[index - 1] = target_list[index - 1], target_list[index]
            # Swap in layout
            target_layout.removeWidget(card)
            target_layout.insertWidget(index - 1, card)
            self.save_data()
            
    def on_move_down(self):
        card = self.sender()
        
        target_list, target_layout = None, None
        if card in self.column_1_widgets:
            target_list, target_layout = self.column_1_widgets, self.column_1_layout
        elif card in self.column_2_widgets:
            target_list, target_layout = self.column_2_widgets, self.column_2_layout
        else:
            return

        index = target_list.index(card)
        if index < len(target_list) - 1: # Can move down
            # Swap in list
            target_list[index], target_list[index + 1] = target_list[index + 1], target_list[index]
            # Swap in layout
            target_layout.removeWidget(card)
            target_layout.insertWidget(index + 1, card)
            self.save_data()

    def on_switch_col(self):
        card = self.sender()
        
        if card in self.column_1_widgets:
            # Remove from col 1
            self.column_1_widgets.remove(card)
            self.column_1_layout.removeWidget(card)
            # Add to top of col 2
            self.column_2_widgets.insert(0, card)
            self.column_2_layout.insertWidget(0, card)
        elif card in self.column_2_widgets:
            # Remove from col 2
            self.column_2_widgets.remove(card)
            self.column_2_layout.removeWidget(card)
            # Add to top of col 1
            self.column_1_widgets.insert(0, card)
            self.column_1_layout.insertWidget(0, card)
        
        self.save_data()

    # --- apply_stylesheet ---
    def apply_stylesheet(self):
        # --- MODIFIED: Added styles for new buttons ---
        style = """
        /* ... (Main styles are unchanged) ... */
        
        QMainWindow, QWidget {
            background-color: #000000; color: #F0F0F0;
            font-family: Inter, Segoe UI, sans-serif; font-size: 10pt;
        }
        QPushButton {
            background-color: #2A2A2A; color: #F0F0F0;
            border: 1px solid #333333; border-radius: 8px;
            padding: 8px 16px; font-weight: 500;
        }
        QPushButton:hover { background-color: #3A3A3A; }
        QPushButton:pressed { background-color: #4A4A4A; }
        QPushButton#AddButton {
            background-color: #007AFF; color: white; border: none;
        }
        QPushButton#AddButton:hover {
            background-color: #006DE0;
        }
        QCheckBox {
            spacing: 8px; padding: 8px 0; color: #F0F0F0;
        }
        QCheckBox::indicator { width: 20px; height: 20px; }
        QScrollArea { border: none; }
        QScrollArea QWidget { background-color: transparent; }
        
        /* ... (Scrollbar styles are unchanged) ... */
        QScrollBar:vertical {
            border: none; background-color: #000000;
            width: 10px; margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #3A3A3A; border-radius: 5px;
            min-height: 20px;
        }
        /* ... (rest of scrollbar) ... */


        /* --- Sentence Card --- */
        QFrame#SentenceCard {
            background-color: #1C1C1C; border-radius: 12px;
            border: 1px solid #333333;
        }
        QLabel { background-color: transparent; color: #F0F0F0; }
        
        /* --- REMOVED Drag Handle Style --- */
        
        QLabel#PlaceholderLabel {
            color: #555555; font-size: 14pt;
        }
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

        /* --- NEW: Reorder Button Styles --- */
        QPushButton#MoveUpButton, QPushButton#MoveDownButton, QPushButton#SwitchColButton {
            background-color: #333333;
            color: #AAAAAA;
            font-weight: 600;
            border: 1px solid #444444;
            padding: 4px; /* Reset padding */
            border-radius: 6px;
        }
        QPushButton#MoveUpButton:hover, QPushButton#MoveDownButton:hover, QPushButton#SwitchColButton:hover {
            background-color: #444444;
            color: #FFFFFF;
        }
        /* --- */

        /* --- Text Input Fields --- */
        QLineEdit {
            background-color: #1A1A1A; border: 1px solid #333333;
            border-radius: 8px; padding: 8px 12px;
            font-size: 10pt; color: #F0F0F0;
        }
        QLineEdit:focus { border: 1px solid #007AFF; }
        
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


# --- 5. Run the Application ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())