import rumps
import pyperclip
import json
import os
from AppKit import NSEvent, NSEventModifierFlagOption, NSEventModifierFlagCommand

DATA_FILE = os.path.join(os.path.expanduser("~"), ".clipboard_history_data.json")

class ClipboardHistoryApp(rumps.App):
    def __init__(self):
        super(ClipboardHistoryApp, self).__init__("📋")
        
        self.history = []
        self.pinned = []
        self.max_history = 10
        self.last_clip = ""
        
        self.load_data()
        self.update_menu()

    def save_data(self):
        data = {
            "history": self.history,
            "pinned": self.pinned
        }
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    self.pinned = data.get("pinned", [])
            except Exception:
                pass

    @rumps.timer(1)
    def check_clipboard(self, _):
        current_clip = pyperclip.paste()
        if current_clip and current_clip != self.last_clip:
            self.last_clip = current_clip
            self.add_history(current_clip)

    def add_history(self, text):
        if text in self.pinned:
            return

        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        
        if len(self.history) > self.max_history:
            self.history.pop()
            
        self.save_data()
        self.update_menu()

    def update_menu(self):
        self.menu.clear()
        # ヘルプ表示を更新
        self.menu.add(rumps.MenuItem("💡 Opt:ピン留め / Cmd:全文表示"))
        self.menu.add(rumps.separator)

        if self.pinned:
            for item in self.pinned:
                self.create_menu_item(item, is_pinned=True)
            self.menu.add(rumps.separator)

        if not self.history:
            self.menu.add(rumps.MenuItem("（履歴なし）"))
        else:
            for item in self.history:
                self.create_menu_item(item, is_pinned=False)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("履歴をクリア", callback=self.clear_history))
        self.menu.add(rumps.MenuItem("終了", callback=rumps.quit_application))

    def create_menu_item(self, full_text, is_pinned):
        # 【変更点1】 表示文字数を 50文字 に増やしました
        limit = 50
        display_text = full_text[:limit].replace('\n', ' ') + ("..." if len(full_text) > limit else "")
        
        if is_pinned:
            title = f"📌 {display_text}"
        else:
            title = f"      {display_text}"

        menu_item = rumps.MenuItem(title, callback=self.on_item_click)
        menu_item.full_text = full_text
        menu_item.is_pinned = is_pinned
        self.menu.add(menu_item)

    def on_item_click(self, sender):
        text = sender.full_text
        is_pinned = sender.is_pinned

        flags = NSEvent.modifierFlags()
        
        # 【変更点2】 Commandキー (⌘) が押されているかチェック
        if flags & NSEventModifierFlagCommand:
            # 全文をポップアップウィンドウで表示
            rumps.alert(title="全文表示", message=text, ok="閉じる")
            
        # Optionキー (Alt) が押されているかチェック
        elif flags & NSEventModifierFlagOption:
            if is_pinned:
                self.unpin_item(text)
            else:
                self.pin_item(text)
        else:
            # 何も押していなければコピー
            self.copy_to_clipboard(text)

    def copy_to_clipboard(self, text):
        pyperclip.copy(text)
        self.last_clip = text
        rumps.notification("コピー", "", f"クリップボードにコピーしました")

    def pin_item(self, text):
        if text not in self.pinned:
            self.pinned.insert(0, text)
            if text in self.history:
                self.history.remove(text)
            self.save_data()
            self.update_menu()
            rumps.notification("ピン留め", "", "アイテムを固定しました")

    def unpin_item(self, text):
        if text in self.pinned:
            self.pinned.remove(text)
            self.history.insert(0, text)
            self.save_data()
            self.update_menu()
            rumps.notification("解除", "", "ピン留めを解除しました")

    def clear_history(self, _):
        self.history = []
        self.save_data()
        self.update_menu()
        rumps.notification("履歴クリア", "", "通常の履歴を削除しました")

if __name__ == "__main__":
    ClipboardHistoryApp().run()